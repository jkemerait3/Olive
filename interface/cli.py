import json
import os
import csv
from datetime import datetime
from llm.local_llm import query_phi_model

INVENTORY_DIR = "inventories"
OUTPUT_DIR = "output"

def run_cli_chatbot():
    print("Welcome to the Mental Health Inventory Chatbot")
    user_input = input("Please describe your symptoms:\nYou: ")

    # Step 1: Ask LLM what inventories to run
    prompt = (
        f"Given the user's self-report: \"{user_input}\", and your background knowledge of mental health symptoms, "
        f"which inventories would be most appropriate to help a clinician understand this case?"
        f"Respond with a list of inventory filenames (without extensions) from the following set:\n"
        f"{os.listdir(INVENTORY_DIR)}"
    )
    llm_response = query_phi_model(prompt)

    # Step 2: Parse selected inventories
    selected_files = [
        f.strip().lower().replace('.json', '') + ".json"
        for f in llm_response.split()
        if f.strip().lower().endswith('.json') or f.strip().lower() in [name[:-5] for name in os.listdir(INVENTORY_DIR)]
    ]
    selected_files = [f for f in selected_files if f in os.listdir(INVENTORY_DIR)]

    if not selected_files:
        print("No valid inventories suggested. Exiting.")
        return

    # Step 3: Administer inventories and collect results
    results = []
    for inv_file in selected_files:
        with open(os.path.join(INVENTORY_DIR, inv_file)) as f:
            inventory = json.load(f)
        score = 0
        for q in inventory["questions"]:
            print(f"Q{q['id']}: {q['text']}")
            for idx, opt in enumerate(q["options"]):
                print(f"  {idx + 1}. {opt['label']}")
            try:
                ans = int(input("Your answer (1-4): ").strip()) - 1
                score += q["options"][ans]["value"]
            except:
                score += 0
        interpretation = ""
        for level in inventory["scoring"]["interpretation"]:
            if level["min"] <= score <= level["max"]:
                interpretation = level["label"]
                break
        results.append({
            "inventory": inventory["title"],
            "score": score,
            "interpretation": interpretation
        })

    # Step 4: Export results to CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"inventory_results_{timestamp}.csv")
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["inventory", "score", "interpretation"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Inventory results saved to: {output_file}")
