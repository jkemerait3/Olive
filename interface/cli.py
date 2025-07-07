import csv
import os
from llm.local_llm import query_llm
from utils import load_inventory, administer_inventory

def get_patient_info():
    print("Welcome to the Mental Health Screening Chatbot.")
    first_name = input("Please enter your first name: ")
    last_name = input("Please enter your last name: ")
    dob = input("Please enter your date of birth (MM/DD/YYYY): ")
    return first_name, last_name, dob

def get_self_report():
    print("\nPlease describe what brings you in today (your symptoms and concerns):")
    return input("> ")

def generate_csv_output(patient_info, self_report, assessment_summary, results, filename="output/results.csv"):
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)

        # Row 1: patient info + summary
        metadata_row = [
            f"{patient_info[0]} {patient_info[1]}",
            patient_info[2],
            self_report,
            assessment_summary
        ]
        writer.writerow(metadata_row)

        # Row 2: column headers
        max_qs = max(len(r["question_scores"]) for r in results)
        header_row = ["assessment name", "total score"] + [f"q{i+1} score" for i in range(max_qs)]
        writer.writerow(header_row)

        # Row 3+: one row per assessment
        for r in results:
            row = [r["name"], r["total_score"]] + r["question_scores"]
            row += [""] * (len(header_row) - len(row))  # pad
            writer.writerow(row)

    print(f"\n✅ Results saved to {filename}")

def run_cli():
    # Step 1: info + self-report
    patient_info = get_patient_info()
    self_report = get_self_report()

    # Step 2: always run PHQ-4
    print("\nNow administering PHQ-4...")
    phq4_inventory = load_inventory("inventories/PHQ-4.json")
    phq4_result = administer_inventory(phq4_inventory)

    # Step 3: list available inventories (excluding PHQ-4)
    available_files = sorted([
        f for f in os.listdir("inventories")
        if f.endswith(".json") and f != "PHQ-4.json"
    ])

    # Ask LLM which inventories to run
    prompt = (
        "You are assisting a mental health intake chatbot.\n"
        "Based on the patient's self-report and PHQ-4 scores, select the most relevant inventories to administer.\n"
        "ONLY choose from this list of JSON filenames:\n"
        f"{available_files}\n"
        "Do NOT include PHQ-4 again.\n"
        "Respond ONLY with a Python list of filenames to administer, like: ['IES-R.json', 'SPIN.json']\n\n"
        f"Self-report: {self_report}\n"
        f"PHQ-4 scores: {phq4_result['question_scores']}\n"
    )

    chosen_files = query_llm(prompt)
    try:
        chosen = eval(chosen_files) if isinstance(chosen_files, str) else chosen_files
    except:
        print("⚠️ Could not parse LLM response. No additional inventories will be administered.")
        chosen = []

    # Step 4: filter for only known valid filenames
    filtered_chosen = [f for f in chosen if f in available_files]

    # Step 5: administer selected inventories
    results = [phq4_result]
    for filename in filtered_chosen:
        try:
            print(f"\nNow administering: {filename}")
            inventory = load_inventory(f"inventories/{filename}")
            result = administer_inventory(inventory)
            results.append(result)
        except Exception as e:
            print(f"❌ Failed to administer {filename}: {e}")

    # Step 6: generate summary
    prompt_summary = (
        "Here is a transcript of the patient's self-report and the results of the administered inventories. "
        "Write a short summary (2–4 sentences) of the most likely diagnostic concerns and next steps for a human provider. "
        "Do not include scores or names of specific inventories in your summary.\n\n"
        f"Self-report: {self_report}\n\n"
        f"Scores: {[{r['name']: r['total_score']} for r in results]}"
    )
    summary = query_llm(prompt_summary)

    # Step 7: export CSV
    from utils import generate_output_filename
    filename = generate_output_filename(patient_info[0], patient_info[1], patient_info[2])
    generate_csv_output(patient_info, self_report, summary, results, filename)