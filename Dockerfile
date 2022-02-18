# Use Python 3.7
FROM python:3.7

# Copy requirements.txt to the docker image and install packages
COPY requirements.txt /
RUN pip install -r requirements.txt

# Copy files to app folder
COPY . /app

# Expose port 80
EXPOSE 443
ENV PORT 443

# Set the WORKDIR to be the app folder
WORKDIR /app

# Set JAVA_HOME
RUN chmod +x run.sh && \
    apt-get update && \
    apt install -y software-properties-common && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EA8CACC073C3DB2A && \
    add-apt-repository ppa:linuxuprising/java && \
    apt-get update && \
    apt-get -y install openjdk-11-jdk && \
    apt-get install -y ant && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/ && \
    rm -rf /var/cache/oracle-jdk11-installer;

ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

# Use gunicorn as the entrypoint
CMD ./run.sh