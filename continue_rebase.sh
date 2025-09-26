#!/bin/bash

# Script to continue rebase automatically when conflicts are auto-resolved
# This handles the repetitive add + continue cycle when git has already resolved conflicts

while git status --porcelain | grep -q "^UU\|^AA\|^DD\|^AU\|^UA\|^UD\|^DU"; do
    echo "Conflicts detected, checking for auto-resolved conflicts..."
    
    # Add all resolved conflicts
    git add -A
    
    # Handle PROTECTED directories (.cursor, .github) - take main's version
    git checkout --theirs .cursor .github 2>/dev/null || true
    git add .cursor .github 2>/dev/null || true
    
    echo "Continuing rebase..."
    if ! git rebase --continue; then
        echo "Rebase conflict that needs manual intervention. Exiting."
        exit 1
    fi
    
    echo "Rebase step completed."
    
    # Check if rebase is still in progress
    if ! git status | grep -q "rebase in progress"; then
        echo "Rebase completed successfully!"
        exit 0
    fi
done

echo "No conflicts detected or rebase completed."