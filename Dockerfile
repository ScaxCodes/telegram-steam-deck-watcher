# Use an official Python runtime as the base image
FROM python:3.11-slim

# Install Chrome
RUN apt-get update && apt-get install -y wget curl unzip \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables (optional, can also be set in Railway UI)
ENV BOT_TOKEN=your_bot_token
ENV CHAT_ID=your_chat_id

# Run the bot
CMD ["python", "your_script.py"]
