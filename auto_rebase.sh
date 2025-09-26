#!/bin/bash

# Enhanced script to handle rebase conflicts automatically
set -e

echo "Starting automatic rebase conflict resolution..."

while true; do
    # Check if rebase is still in progress
    if ! git status | grep -q "rebase in progress"; then
        echo "Rebase completed successfully!"
        break
    fi
    
    # Check for conflicts
    if git status --porcelain | grep -q "^UU\|^AA\|^DD\|^AU\|^UA\|^UD\|^DU"; then
        echo "Resolving conflicts..."
        
        # Handle PROTECTED directories first (.cursor, .github) - always take main's version
        if git status --porcelain | grep -E "^(UU|AA|DD|AU|UA|UD|DU).*\.cursor" > /dev/null 2>&1; then
            echo "Resolving .cursor conflicts by taking main's version..."
            git checkout --theirs .cursor 2>/dev/null || true
        fi
        
        if git status --porcelain | grep -E "^(UU|AA|DD|AU|UA|UD|DU).*\.github" > /dev/null 2>&1; then
            echo "Resolving .github conflicts by taking main's version..."
            git checkout --theirs .github 2>/dev/null || true
        fi
        
        # Add all resolved files
        git add -A
        
        echo "Continuing rebase..."
        git rebase --continue
    else
        echo "No conflicts detected."
        break
    fi
    
    sleep 1  # Brief pause to avoid overwhelming output
done

echo "Rebase process completed!"