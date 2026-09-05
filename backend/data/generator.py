import os
import json
import random
import pandas as pd
import argparse
from pathlib import Path
from data.seed import set_seed, get_faker, GLOBAL_SEED
from data.scenarios import ScenarioGenerator

def generate_dataset(total_records: int):
    print(f"Generating {total_records} synthetic cases with seed {GLOBAL_SEED}...")
    
    set_seed()
    fake = get_faker()
    sg = ScenarioGenerator(fake)
    
    # Define scenarios and their approximate distributions
    scenarios = [
        (sg.s1_temporary_degradation, 0.15),
        (sg.s2_insufficient_funds, 0.35),
        (sg.s3_hard_decline, 0.15),
        (sg.s4_high_value_uncertain, 0.05),
        (sg.s5_method_specific_issue, 0.10),
        (sg.s6_repeated_recovery_failure, 0.10),
        (sg.s7_unknown_failure, 0.10)
    ]
    
    methods, weights = zip(*scenarios)
    
    data_rows = []
    
    for _ in range(total_records):
        # Select a scenario based on weights
        chosen_scenario = random.choices(methods, weights=weights)[0]
        
        # Generate the case
        case_data = chosen_scenario()
        
        # Flatten into a single dict for Pandas
        row = {
            "scenario": chosen_scenario.__name__,
            **case_data["input"],
            **case_data["ground_truth"]
        }
        data_rows.append(row)
        
    df = pd.DataFrame(data_rows)
    return df

def split_and_save(df: pd.DataFrame, output_dir: str):
    # Fixed sizes
    n_dev = 7000
    n_val = 1500
    n_test = 1500
    
    if len(df) != (n_dev + n_val + n_test):
        raise ValueError(f"Expected 10000 records, got {len(df)}")
        
    # Shuffle predictably (seed is set)
    df_shuffled = df.sample(frac=1, random_state=GLOBAL_SEED).reset_index(drop=True)
    
    dev_df = df_shuffled.iloc[:n_dev]
    val_df = df_shuffled.iloc[n_dev : n_dev + n_val]
    test_df = df_shuffled.iloc[n_dev + n_val :]
    
    os.makedirs(output_dir, exist_ok=True)
    
    dev_df.to_csv(os.path.join(output_dir, "development.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "validation.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "held_out.csv"), index=False)
    
    # Save metadata
    metadata = {
        "seed": GLOBAL_SEED,
        "total_cases": len(df),
        "split": {
            "development": len(dev_df),
            "validation": len(val_df),
            "held_out": len(test_df)
        },
        "scenarios": df["scenario"].value_counts().to_dict(),
        "recoverable_rate": df["recoverable"].mean()
    }
    
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("\nDataset generation complete.")
    print(f"Development: {len(dev_df)}")
    print(f"Validation: {len(val_df)}")
    print(f"Held-out: {len(test_df)}")
    
    print("\nScenario Distribution:")
    for s, count in metadata["scenarios"].items():
        print(f"  {s}: {count} ({count/len(df)*100:.1f}%)")
        
    print(f"\nOverall Recoverable Rate: {metadata['recoverable_rate']*100:.1f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output", help="Output directory relative to data folder")
    parser.add_argument("--count", type=int, default=10000, help="Total records to generate")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent
    out_path = base_path / args.output
    
    df = generate_dataset(args.count)
    split_and_save(df, str(out_path))
