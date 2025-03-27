#!/bin/bash
# Test commands for the Gutenberg Book Analysis API

# Base URL - change this to your actual backend URL
BASE_URL="http://localhost:8000"

# Test 1: Check if API is running
echo "=== Testing if API is running ==="
curl -X GET "$BASE_URL/"

# Test 2: Fetch book data for Romeo and Juliet (ID: 1787)
echo -e "\n\n=== Fetching book data for Romeo and Juliet ==="
curl -X POST \
  "$BASE_URL/api/book" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "1787"}'

# Test 3: Fetch book data for Pride and Prejudice (ID: 1342)
echo -e "\n\n=== Fetching book data for Pride and Prejudice ==="
curl -X POST \
  "$BASE_URL/api/book" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "1342"}'

# Test 4: Start analysis for Romeo and Juliet
echo -e "\n\n=== Starting analysis for Romeo and Juliet ==="
curl -X POST \
  "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "1787"}'

# Test 5: Check analysis status for Romeo and Juliet
echo -e "\n\n=== Checking analysis status for Romeo and Juliet ==="
curl -X GET "$BASE_URL/api/analysis-status/1787"

# Test 6: Get analysis results for Romeo and Juliet (may return 202 if not complete)
echo -e "\n\n=== Getting analysis results for Romeo and Juliet ==="
curl -X GET "$BASE_URL/api/analysis/1787"

# Test 7: Test with invalid book ID
echo -e "\n\n=== Testing with invalid book ID ==="
curl -X POST \
  "$BASE_URL/api/book" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "9999999999"}'

# Test 8: Fetch a different type of book (Alice in Wonderland, ID: 11)
echo -e "\n\n=== Fetching Alice in Wonderland ==="
curl -X POST \
  "$BASE_URL/api/book" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "11"}'

# Test 9: Start analysis for a short book (The Gift of the Magi, ID: 7256)
echo -e "\n\n=== Starting analysis for a short book ==="
curl -X POST \
  "$BASE_URL/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"book_id": "7256"}'