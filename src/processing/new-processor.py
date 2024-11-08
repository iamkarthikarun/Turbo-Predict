import pandas as pd
import joblib

def preprocess_dataframe_and_save(ipfilepath, opfilepath, engine_class):
    try:
        df = pd.read_csv(ipfilepath)

        engine_class = str(engine_class)

        df['engine_class'] = df['engine_class'].apply(lambda x: str(int(round(x))) if not pd.isna(x) else x)

        filtered_df = df[df['engine_class'] == engine_class]
        print(filtered_df.columns)
        if(engine_class=='4'):
            if 'time_cycles' in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by='time_cycles', ascending=True)

            selected_features = ['time_cycles', 'unit_nr', 'setting_1', 'setting_3', 'T2', 'T24', 'T30', 'T50',
       'P2', 'P15', 'Nc', 'Ps30', 'phi', 'NRf', 'NRc', 'BPR', 'farB',
       'htBleed', 'Nf_dmd', 'PCNfR_dmd', 'W31', 'W32']
            
            processed_data = filtered_df[selected_features]
            processed_data.to_csv(opfilepath, index=False)
            print(f"Preprocessed data saved to: {opfilepath}")

            return
        
        if 'time_cycles' in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by='time_cycles', ascending=True)

        selected_features = ['time_cycles', 'unit_nr', 'T24', 'T30', 'T50', 'P15', 'P30', 'Nf', 'Nc', 'Ps30', 'phi', 'NRf', 'BPR', 'htBleed', 'W31', 'W32']
        
        processed_data = filtered_df[selected_features]
        processed_data.to_csv(opfilepath, index=False)
        print(f"Preprocessed data saved to: {opfilepath}")

    except Exception as e:
        print(f"Error preprocessing data: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess DataFrame and save it")
    parser.add_argument("--ipfilepath", type=str, help="Path to the input CSV file")
    parser.add_argument("--opfilepath", type=str, help="Path to the output CSV file")
    parser.add_argument("--engine_class", type=str, help="Engine class to filter")
    args = parser.parse_args()

    preprocess_dataframe_and_save(args.ipfilepath, args.opfilepath, args.engine_class)
