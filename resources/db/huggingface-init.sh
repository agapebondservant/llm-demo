echo "Setting up huggingface cache directories..."
mkdir -p /opt/cache/huggingface/transformers
chown -R postgres /opt/cache/
echo "Setup completed."