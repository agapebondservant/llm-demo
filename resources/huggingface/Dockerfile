FROM python:3.10
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
&& apt-get update -y \
&& apt-get install git-lfs python3-pip -y \
&& pip3 install huggingface_hub[cli] transformers --break-system-packages \
&& git lfs install