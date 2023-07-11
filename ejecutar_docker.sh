docker build -t pyteg .
docker run -it --rm -v ./:/app --name pyteg pyteg /bin/bash
