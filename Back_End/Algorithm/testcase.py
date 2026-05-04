import os

import pandas as pd

from Back_End.Algorithm.optimizer import generate_candidates


def _load_sample_data():
    data_path = os.path.join(os.getcwd(), "Back_End", "Database", "data.json")
    df = pd.read_json(data_path, encoding="utf-8", dtype={"id": str})

    df_sang = df[df["meals"].apply(lambda meals: "sáng" in meals)].head(10)
    df_trua = df[df["meals"].apply(lambda meals: "trưa" in meals)].head(10)
    df_toi = df[df["meals"].apply(lambda meals: "tối" in meals)].head(10)

    return [{"sáng": df_sang}, {"trưa": df_trua}, {"tối": df_toi}]


def run_testcase():
    candidate_pool = _load_sample_data()
    user_budget = 500000
    user_lat = 16.067
    user_lng = 108.234

    print("User location:", user_lat, user_lng)
    results = generate_candidates(candidate_pool, budget=user_budget, top_n=5)
    print("Top routes:")
    for idx, route in enumerate(results, start=1):
        print("#", idx)
        print(route)


if __name__ == "__main__":
    run_testcase()
