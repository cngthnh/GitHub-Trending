#!/usr/bin/env python

from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import Row, SQLContext
import json
import const
import requests

UPDATE_DATA_URL = 'https://localhost/update'

conf = SparkConf()
conf.setAppName("YouTubeCommentsStreaming")

sparkContext = SparkContext(conf=conf)
sparkContext.setLogLevel("ERROR")

def splitLangs(line):
    [keyword, langs] = line.split("$$$")

    result = map(lambda x: (keyword, x), langs.split("\t"))

    return list(result)

def sendToDashboard(rows, langs):
    data = {}

    for row in rows:
        row = json.loads(row)
        data[row['lang']] = data.get(row['lang'], dict.fromkeys(const.KEYWORDS))
        data[row['lang']][row['keyword']] = row['lang_count']
    
    for lang in langs:
        data[lang] = list(data[lang].values())

    requests.post(url=UPDATE_DATA_URL, json=data)
    

def processRDD(time, rdd):
        print("----------- %s -----------" % str(time))
        try:
            sql_context = getSparkSqlContext(rdd.context)
            row_rdd = rdd.map(lambda w: Row(keyword=w[0][0], lang=w[0][1], lang_count=w[1]))
            keywords_df = sql_context.createDataFrame(row_rdd)
            keywords_df.registerTempTable("keywords")
            keywords_counts_df = sql_context.sql("select keyword, lang, lang_count from keywords order by lang_count desc")
            langs_list = keywords_counts_df.select('lang').distinct().rdd.map(lambda x: x.lang).collect()

            sendToDashboard(keywords_counts_df.toJSON().collect(), langs_list)

        except Exception as e:
            print(e)

def getSparkSqlContext(spark_context):
    if ('sparkSqlContext' not in globals()):
        globals()['sparkSqlContext'] = SQLContext(spark_context)
    return globals()['sparkSqlContext']

def aggWordsCount(new_values, total_sum):
    total_sum = total_sum if total_sum else 0
    count = [field for field in new_values]

    return total_sum + sum(count)

sparkStreamingContext = StreamingContext(sparkContext, 2)
sparkStreamingContext.checkpoint("GitHubRepos")
dataStream = sparkStreamingContext.socketTextStream("localhost", 1205)

words = dataStream.flatMap(splitLangs)
words = words.map(lambda x: ((x[0], x[1]), (1)))

wordsCount = words.updateStateByKey(aggWordsCount)
wordsCount.foreachRDD(processRDD)

sparkStreamingContext.start()
sparkStreamingContext.awaitTermination()
