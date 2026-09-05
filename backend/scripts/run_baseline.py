import pandas as pd
import argparse
from pathlib import Path
from app.core.baseline import BaselinePolicy


def run_baseline(input_csv: str, output_csv: str):
    print(f"Running baseline policy on {input_csv}...")
    df = pd.read_csv(input_csv)
    policy = BaselinePolicy()

    baseline_actions = []
    simulated_outcomes = []
    recovered_amounts = []

    for _, row in df.iterrows():
        event = row.to_dict()
        action = policy.evaluate(event)

        ground_truth = {
            "recoverable": event.get("recoverable", False),
            "best_action": event.get("best_action"),
            "amount_recovered": event.get("amount_recovered", 0.0)
        }

        success, amount = policy.simulate_outcome(action, ground_truth)

        baseline_actions.append(action)
        simulated_outcomes.append(success)
        recovered_amounts.append(amount)

    df["baseline_action"] = baseline_actions
    df["simulated_outcome"] = simulated_outcomes
    df["recovered_amount"] = recovered_amounts

    # Store results
    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    success_rate = sum(simulated_outcomes) / len(simulated_outcomes)
    total_recovered = sum(recovered_amounts)
    max_possible = df["amount_recovered"].sum()

    print("\nBaseline Results:")
    print(f"Total Cases: {len(df)}")
    print(f"Success Rate: {success_rate * 100:.2f}%")
    print(f"Total Recovered: ${total_recovered:.2f}")
    print(f"Max Possible Recovery: ${max_possible:.2f}")
    print(
        f"Efficiency: {(total_recovered / max_possible * 100) if max_possible else 0:.2f}%")
    print(f"\nResults saved to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/output/development.csv")
    parser.add_argument("--output", default="data/output/baseline_results.csv")
    args = parser.parse_args()

    run_baseline(args.input, args.output)
