#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <path_to_xml>"
  exit 1
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
  echo -e "\033[0;31m❌ FAIL\033[0m: File not found: $FILE"
  exit 1
fi

SCORE=0
MAX_SCORE=9

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Validating Persona XML: $FILE"
echo "----------------------------------------"

# 1. 9 layers check
layers=(
  "identity_and_persona"
  "objective_and_scope"
  "reasoning_framework"
  "operational_constraints"
  "meta_cognition_control"
  "chain_of_verification"
  "emotional_behavioral_profile"
  "output_contract"
  "few_shot_examples"
)

for layer in "${layers[@]}"; do
  if grep -q "<$layer" "$FILE"; then
    echo -e "${GREEN}✅ PASS${NC}: Layer <$layer> found."
    SCORE=$((SCORE + 1))
  else
    echo -e "${RED}❌ FAIL${NC}: Layer <$layer> is missing."
  fi
done

echo "----------------------------------------"

# 2. Sandwich Tail Check
if grep -q "<persona_reinforcement_anchor>" "$FILE"; then
  echo -e "${GREEN}✅ PASS${NC}: Sandwich Anchor <persona_reinforcement_anchor> found."
else
  echo -e "${RED}❌ FAIL${NC}: Sandwich Anchor <persona_reinforcement_anchor> is missing."
fi

# 3. Placeholder Check
placeholders=$(grep -o '{{[^}]*}}' "$FILE" | wc -l)
if [ "$placeholders" -gt 0 ]; then
  echo -e "${YELLOW}⚠️ WARNING${NC}: Found $placeholders unreplaced {{PLACEHOLDER}} variables."
else
  echo -e "${GREEN}✅ PASS${NC}: No unreplaced placeholders found."
fi

# 4. Empty check
for layer in "${layers[@]}"; do
  content=$(sed -n "/<$layer>/,/<\/$layer>/p" "$FILE" | grep -v "<$layer" | grep -v "<\/$layer>" | tr -d '[:space:]')
  if [ -z "$content" ]; then
    echo -e "${YELLOW}⚠️ WARNING${NC}: Layer <$layer> appears to be empty."
  fi
done

echo "----------------------------------------"
echo "Final Score: $SCORE / $MAX_SCORE"

if [ "$SCORE" -eq "$MAX_SCORE" ]; then
  echo -e "${GREEN}All required layers are present!${NC}"
else
  echo -e "${RED}Some required layers are missing.${NC}"
fi
