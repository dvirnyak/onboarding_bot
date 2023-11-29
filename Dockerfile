FROM ubuntu:latest

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip

# Set the working directory
WORKDIR /app

# Copy the project files to the container
COPY . .

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get install -y net-tools iputils-ping dnsutils

# Install project dependencies
RUN pip3 install -r requirements.txt

# Set the entrypoint command to start the bot
CMD ["python3", "start_bot.py"]
