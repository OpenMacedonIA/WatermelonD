#!/bin/bash

# update_grape_models.sh
# Checks for updates in Grape model repositories.

MODELS_DIR="$(dirname "$0")/../../models"

echo "=== Auto-Update Grape Models ==="
date

# Function to update a git repo
update_repo() {
    REPO_DIR="$1"
    NAME="$2"
    
    if [ -d "$REPO_DIR/.git" ]; then
        echo "Checking updates for $NAME..."
        cd "$REPO_DIR"
        git fetch
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse @{u})
        
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "Updates found for $NAME. Pulling..."
            git pull
            if [ $? -eq 0 ]; then
                echo "$NAME updated successfully."
            else
                echo "Error updating $NAME."
            fi
        else
            echo "$NAME is up to date."
        fi
    else
        echo "Directory $REPO_DIR is not a git repository or does not exist."
    fi
}

update_repo "$MODELS_DIR/chardonnay" "Grape-Chardonnay"
update_repo "$MODELS_DIR/malbec" "Grape-Malbec"
update_repo "$MODELS_DIR/pinot" "Grape-Pinot"

echo "=== Update Check Complete ==="
