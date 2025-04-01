docker build --no-cache -t img-pyteg .
docker run -it --rm -v ./:/app --name pyteg img-pyteg /bin/sh
