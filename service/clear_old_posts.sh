#!/bin/bash

### NOTE(Tej): This may be helpful if you have lots of old posts slowing down
### your server. It looks for posts older than 30min and clears them out.
echo "Clearing old posts:"
find ./private -maxdepth 1 -mmin +30 -name 'post*' -type f -print -exec rm -f {} \;
