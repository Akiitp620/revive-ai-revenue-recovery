import pandas as pd
from data.generator import generate_dataset, split_and_save


def test_reproducibility(tmp_path):
    # Generate twice
    df1 = generate_dataset(100)
    df2 = generate_dataset(100)

    # Must be exactly identical
    pd.testing.assert_frame_equal(df1, df2)


def test_split_counts(tmp_path):
    df = generate_dataset(10000)

    output_dir = tmp_path / "output"
    split_and_save(df, str(output_dir))

    dev_df = pd.read_csv(output_dir / "development.csv")
    val_df = pd.read_csv(output_dir / "validation.csv")
    test_df = pd.read_csv(output_dir / "held_out.csv")

    assert len(dev_df) == 7000
    assert len(val_df) == 1500
    assert len(test_df) == 1500
    assert (len(dev_df) + len(val_df) + len(test_df)) == 10000
