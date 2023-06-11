echo "Setting up huggingface cache directories..."
mkdir -p /opt/cache/huggingface/transformers
chown -R 1001 /opt/cache/
echo "Setup completed."