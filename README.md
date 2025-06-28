# Sokół Availability Checker

A Python script that monitors the availability of training slots on klubsokol.nakiedy.pl. When slots become available, it sends notifications via ntfy.sh.

## Features

- Automatically checks for available training slots
- Runs checks on Wednesday, Thursday, and Friday
- Sends notifications when slots are found
- Logs all activities to both console and file
- Can run on both x86 and ARM (Raspberry Pi) architectures

## Prerequisites

- Docker installed on your system
- Internet connection
- Access to ntfy.sh (for notifications)

## Installation

### Building the Docker Image

1. Clone this repository:
```bash
git clone <repository-url>
cd windsurf-project
```

2. Build the Docker image:
```bash
docker build -t sokol-checker .
```

Note: The Dockerfile is configured to work on both x86 and ARM architectures (like Raspberry Pi) using Chromium for web automation.

### Running the Container

Run the container with mounted logs directory:
```bash
# Create logs directory if it doesn't exist
mkdir -p logs

# Run the container
docker run -d \
  --name sokol-checker \
  -v $(pwd)/logs:/app/logs \
  sokol-checker
```

### Viewing Logs

To view the logs in real-time:
```bash
# View container logs
docker logs -f sokol-checker

# Or check the log file directly
tail -f logs/sokol_checker.log
```

### Managing the Container

```bash
# Stop the container
docker stop sokol-checker

# Start the container
docker start sokol-checker

# Remove the container
docker rm sokol-checker
```

## How It Works

1. The script runs continuously with the following schedule:
   - Active days: Wednesday, Thursday, Friday
   - On other days, it sleeps until the next checking day
   - Checks are performed every 60 seconds during active days

2. When slots become available:
   - Sends a notification to ntfy.sh
   - Logs the event
   - Takes a break until Monday to avoid spam

3. Logging:
   - All events are logged to `logs/sokol_checker.log`
   - Logs are also displayed in the console output
   - Log files persist between container restarts

## Troubleshooting

1. If the container fails to start:
   - Check if port 9515 is not in use (ChromeDriver port)
   - Ensure the logs directory exists and is writable
   - Check Docker logs for specific errors

2. If notifications aren't working:
   - Verify internet connectivity
   - Check if ntfy.sh is accessible
   - Review logs for any connection errors

## License

This project is open-source and available under the MIT License.
