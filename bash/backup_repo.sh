#!/bin/bash

# Set variables
REPO_URL="https://github.com/IAES-Repo/ICS-Dash.git"
BACKUP_DIR="/home/iaes/iaesDash/backups"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Navigate to backup directory
cd $BACKUP_DIR

# Get the current date
CURRENT_DATE=$(date +%Y%m%d)

# Check if the repository is already cloned
if [ -d "ICS-Dash" ]; then
  echo "Repository already cloned. Pulling the latest changes."
  # Navigate to the repository directory and pull the latest changes
  cd ICS-Dash
  git pull
  cd ..
else
  echo "Cloning the repository."
  # Clone the repository
  git clone $REPO_URL
fi

# Create a zip archive of the backup
echo "Creating a zip archive of the backup."
zip -r ICS-Dash_backup_$CURRENT_DATE.zip ICS-Dash

# Print a completion message
echo "Backup completed successfully. Backup file: ICS-Dash_backup_$CURRENT_DATE.zip"
