#!/usr/bin/env bash
set -euo pipefail

# Upload a build artifact to the downloads S3 bucket.
#
# Usage:
#   ./scripts/publish-artifact.sh <slug> <version> <platform> <file>
#
# Example:
#   ./scripts/publish-artifact.sh mp-1 1.0.0 mac ./build/mp-1-1.0.0-mac.pkg
#
# After uploading, update manifest.json with the printed fileName and size,
# then upload manifest.json separately:
#   aws s3 cp manifest.json s3://$BUCKET/manifest.json --cache-control "public, max-age=300"

BUCKET="metaphase-downloads-$(aws sts get-caller-identity --query Account --output text)"

if [[ $# -lt 4 ]]; then
    echo "Usage: $0 <slug> <version> <platform> <file>"
    echo "Example: $0 mp-1 1.0.0 mac ./build/mp-1-1.0.0-mac.pkg"
    exit 1
fi

SLUG="$1"
VERSION="$2"
PLATFORM="$3"
FILE="$4"

if [[ ! -f "$FILE" ]]; then
    echo "Error: file not found: $FILE"
    exit 1
fi

EXT="${FILE##*.}"
FILE_NAME="${SLUG}-${VERSION}-${PLATFORM}.${EXT}"
S3_KEY="${SLUG}/${FILE_NAME}"
FILE_SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat --printf="%s" "$FILE")

echo "Uploading ${FILE} -> s3://${BUCKET}/${S3_KEY}"
aws s3 cp "$FILE" "s3://${BUCKET}/${S3_KEY}"

echo ""
echo "Upload complete. Add this to manifest.json:"
echo ""
echo "  { \"platform\": \"${PLATFORM}\", \"label\": \"TODO\", \"fileName\": \"${FILE_NAME}\", \"size\": ${FILE_SIZE} }"
echo ""

# Optionally invalidate the CloudFront cache for manifest.json
if [[ "${INVALIDATE_CACHE:-}" == "1" ]]; then
    DIST_ID=$(aws cloudfront list-distributions --query \
        "DistributionList.Items[?Aliases.Items[?contains(@,'downloads.metaphaseindustries.com')]].Id" \
        --output text)
    if [[ -n "$DIST_ID" ]]; then
        echo "Invalidating CloudFront cache for /manifest.json (distribution: ${DIST_ID})"
        aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/manifest.json"
    else
        echo "Warning: could not find CloudFront distribution for downloads.metaphaseindustries.com"
    fi
fi
