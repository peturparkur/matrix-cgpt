# Setup
To run need the following environment variables; does accept .env

### ENVIRONMENT
```
MATRIX_BOT_CGPT_HOME=https://matrix.org
MATRIX_BOT_CGPT_USERNAME=username
MATRIX_BOT_CGPT_PASSWORD=password
MATRIX_BOT_CGPT_CREDPATH=./secrets/example.txt
MATRIX_BOT_CGPT_CGPT_TOKEN=1234
MATRIX_BOT_CGPT_PREFIX=!
MATRIX_BOT_CGPT_LLM_URL=http://localhost:8000 # for OpenAI MATRIX_BOT_CGPT_LLM_URL is not required
```

### VOLUMES
Need to share a given folder or file to store secrets for matrix. see: `MATRIX_BOT_CGPT_CREDPATH`
```
./secrets/example.txt
```

# Usage
In matrix use:
```
!cgpt -m "count to 10"
```

### Clear history
```
!clear
```