# The code to identify the air pollution hotspots using the Three-criteria method explained in Goyal et al., 2021

import importlib.util
import subprocess


packages = ['numpy', 'pandas', 'tkinter', 'matplotlib', 'xlsxwriter']

for package in packages:
    spec = importlib.util.find_spec(package)
    if spec is None:
        print(f"{package} is not installed. Installing...")
        subprocess.run(['pip', 'install', package])
    else:
        print(f"{package} is already installed.")


import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import argparse

args = {}
threshold_value = {}
standard_value = {}

def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path, parse_dates=["Date"], dayfirst=True)
        df = df.replace("NA", pd.NA)
        #process_data(df)
        try:
#             process_data(df)
            process_data(df, threshold_value=args.threshold_value, standard_value=args.standard_value)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during data processing: {str(e)}")
        finally:
            root.destroy() 


def process_data(df, threshold_value, standard_value):
    # Your existing data processing code here
    print(df.head())  # Just printing the head of the DataFrame as an example
    
    # Use the threshold and standard values passed as arguments
    print("Threshold value:", threshold_value)
    print("Standard value:", standard_value)

    # Initialize dictionaries to store places meeting each criterion and the maximum criteria for each month
    places_by_month = {}

    # Initialize a dictionary to store the places meeting all criteria for each month
    places_meeting_all_criteria_by_month = {}

    # Initialize a set to store places meeting all criteria across all months
    places_meeting_all_criteria = set()

    # Create an Excel writer object
    writer1 = pd.ExcelWriter(f'{threshold_value}_places_meeting_each_criterion_by_month.xlsx', engine='xlsxwriter')
    writer2 = pd.ExcelWriter(f'{threshold_value}_places_meeting_all_criteria_by_month.xlsx', engine='xlsxwriter')
    writer3 = pd.ExcelWriter(f'{threshold_value}_places_meeting_all_criteria_hotspots.xlsx', engine='xlsxwriter')
    writer4 = pd.ExcelWriter(f'{threshold_value}_criteria1_data.xlsx', engine='xlsxwriter')
    writer5 = pd.ExcelWriter(f'{threshold_value}_criteria2_data.xlsx', engine='xlsxwriter')
    writer6 = pd.ExcelWriter(f'{threshold_value}_criteria3_data.xlsx', engine='xlsxwriter')

    # Iterate over each month
    for month, data in df.groupby(df["Date"].dt.to_period("M")):
        month_data = data.copy()
        month_data.reset_index(drop=True, inplace=True)  # Reset index to start from 0
        del month_data["Date"]  # Remove the Date column

        # Initialize sets to store places meeting each criterion for this month
        places_meeting_criterion_1 = set()
        places_meeting_criterion_2 = set()
        places_meeting_criterion_3 = set()

        # Iterate over each place
        for place in month_data.columns:
            ################   Criterion 1  ################
            exceed_threshold_count = (month_data[place] > standard_value).sum()
            month_count = len(month_data)
            month_percentage = (exceed_threshold_count / month_count) * 100
            if month_percentage > 60:
                places_meeting_criterion_1.add((place, month_percentage))

           ################   Criterion 2  ################
            monthly_average = month_data[place].mean()
            exceeding_months = monthly_average > threshold_value
            if exceeding_months:
                places_meeting_criterion_2.add((place, monthly_average))

            ################   Criterion 3  ################
            min_consecutive_days = 3
            exceed_threshold = month_data[place] > threshold_value
            consecutive_exceed_count = 0
            consecutive_days_count = 0

            for value in exceed_threshold:
                if value:  # If the value is True (threshold exceeded)
                    consecutive_days_count += 1
                    if consecutive_days_count >= min_consecutive_days:
                        consecutive_exceed_count += 1
                        consecutive_days_count = 0  # Reset count after counting a set of consecutive days
                else:  # If the value is False (threshold not exceeded)
                    consecutive_days_count = 0  # Reset count if consecutive days are broken

            # Now consecutive_exceed_count represents the number of sets of consecutive days where the threshold is exceeded
            if consecutive_exceed_count > 0:
                places_meeting_criterion_3.add((place, consecutive_exceed_count))


        # Store the places meeting each criterion for this month
        places_by_month[month] = {
            "Criterion 1": places_meeting_criterion_1,
            "Criterion 2": places_meeting_criterion_2,
            "Criterion 3": places_meeting_criterion_3
        }

        ################################################# places_meeting_each_criterion_by_month  #############################################################################################
        # Print places meeting each criterion for this month
        print('#################################################################################################')
        print("Month:", month)
        print('#################################################################################################')
        print("Criterion 1:", places_meeting_criterion_1)
        print("Criterion 2:", places_meeting_criterion_2)
        print("Criterion 3:", places_meeting_criterion_3)


        # Create separate DataFrames for each criterion
        sheet_df_criterion1 = pd.DataFrame({"Criterion 1": list(places_meeting_criterion_1)})
        sheet_df_criterion2 = pd.DataFrame({"Criterion 2": list(places_meeting_criterion_2)})
        sheet_df_criterion3 = pd.DataFrame({"Criterion 3": list(places_meeting_criterion_3)})
        # Concatenate DataFrames together
        sheet_df = pd.concat([sheet_df_criterion1, sheet_df_criterion2, sheet_df_criterion3], axis=1)
        # Write the DataFrame to Excel
        sheet_df.to_excel(writer1, sheet_name=f"Month_{month}", index=False)  


        # Print places meeting each criterion for this month
        print('#################################################################################################')
        print("Month:", month)
        print('#################################################################################################')
        print("| Criterion 1 |:", [place for place, _ in places_meeting_criterion_1])
        print("| Criterion 2 |:", [place for place, _ in places_meeting_criterion_2])
        print("| Criterion 3 |:", [place for place, _ in places_meeting_criterion_3])


        # Find the intersection of places meeting all three criteria for this month
        places_meeting_all_criteria = {place for place, _ in places_meeting_criterion_1} & \
                                       {place for place, _ in places_meeting_criterion_2} & \
                                       {place for place, _ in places_meeting_criterion_3}

        ################################################# places_meeting_all_criteria_by_month  #############################################################################################
        # Print the intersection of places meeting all three criteria for this month
        print('')
        print('------------------------------------------------------------------------------------------------')
        print("Intersection of places meeting all criteria for this month:", places_meeting_all_criteria)
        print('------------------------------------------------------------------------------------------------')
        print('')  # Add an empty line for better readability

        # Convert the set to a DataFrame
        df_intersection = pd.DataFrame(list(places_meeting_all_criteria), columns=["Places"])
        # Write the DataFrame to CSV
        df_intersection.to_excel(writer2, sheet_name=f"Month_{month}", index=False)


        ################################################# places_meeting_all_criteria - HOTSPOTS  #############################################################################################
        # Store the places meeting all criteria for this month in the dictionary
        places_meeting_all_criteria_by_month[month] = places_meeting_all_criteria

    # Calculate the intersection of all places meeting all criteria across all months
    intersection_of_all_criteria = set.intersection(*places_meeting_all_criteria_by_month.values())

    # Print the intersection of all places meeting all criteria across all months
    print('')
    print('-+++++++++++++++++++++++++++++++++++++++++ HOTSPOTS +++++++++++++++++++++++++++++++++++++++++++++++++++++-')
    print("Intersection of all places meeting all criteria across all months:")
    print(intersection_of_all_criteria)
    print('-++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-')
    print('')
    # Convert the set to a DataFrame
    df_intersection_all = pd.DataFrame(list(intersection_of_all_criteria), columns=["Places"])
    # Write the DataFrame to CSV
    df_intersection_all.to_excel(writer3, sheet_name=f"Month_{month}", index=False)

    print('')
    print('')


    ###############################################################################################################################################################################
    print('')
    print('                         Details of places meet each Criterion                                  ')
    print('')

    # Initialize empty lists to store data
    c1_data = []
    c2_data = []
    c3_data = []

    # Print the places meeting each criterion for each month
    for month, places in places_by_month.items():
        print('#################################################################################################')
        print(f"Month: {month}")
        print('#################################################################################################')
        for criterion, places_list in places.items():
            # Process Criterion 1
            if criterion == "Criterion 1":
                # Create a string for places meeting Criterion 1
                places_str = ',\n'.join([f"{place[0]} = {place[1]:.2f}%" for place in places_list])

                # Find places with maximum percentage
                max_percentage = max(places_list, key=lambda x: x[1])[1]
                max_places = [place[0] for place in places_list if place[1] == max_percentage]
                if len(max_places) > 1:
                    # Create a string for places with maximum percentage if multiple places have the same maximum value
                    max_places_str = f"Place(s) with maximum percentage:  {', '.join(max_places)} = {max_percentage:.2f}%"
                else:
                    # Create a string for single place with maximum percentage
                    max_places_str = f"Place with maximum percentage:  {max_places[0]} = {max_percentage:.2f}%"

                # Append data to the list
                c1_data.append([month, places_str, max_places_str])

                # Print statements
                print(f"Month: {month}")
                print("Criterion 1:")
                print('------------------------------------------------------------------------------------------------')
                print(places_str)
                print(max_places_str)
                print(' ')

            # Process Criterion 2
            elif criterion == "Criterion 2":
                # Initialize strings for Criterion 2
                places_str = ""
                max_places_str = ""
                # Iterate over places and their monthly averages
                for place, monthly_average in sorted(places_list, key=lambda x: x[0]):
                    # Append each place and its average to the string
                    places_str += f"{place:<14} = {monthly_average:.2f}\n"
                # Find places with maximum average
                max_average = max(places_list, key=lambda x: x[1])[1]
                max_places2 = [place[0] for place in places_list if place[1] == max_average]
                # Create a string for places with maximum average
                max_places_str = f"Place(s) with maximum average:  {', '.join(max_places2)} = {max_average:.2f}"

                # Append data to the list for Criterion 2
                c2_data.append([month, places_str, max_places_str])

                # Print statements for Criterion 2
                print(f"Month: {month}")
                print("Criterion 2:")
                print('------------------------------------------------------------------------------------------------')
                print(places_str)
                print(max_places_str)
                print(' ')

            # Process Criterion 2
            elif criterion == "Criterion 3":
                # Initialize strings for Criterion 3
                places_str = ""
                max_places_str = ""
                # Iterate over places and their total exceeding days
                for place, total_exceeding_days in sorted(places_list, key=lambda x: x[0]):
                    # Append each place and its total exceeding days to the string
                    places_str += f"{place:<15} = {total_exceeding_days}\n"
                # Find the maximum total exceeding days
                max_total_days = max(places_list, key=lambda x: x[1])[1]
                max_places3 = [place[0] for place in places_list if place[1] == max_total_days]
                # Create a string for places with maximum total exceeding days
                max_places_str = f"Place(s) with maximum total exceeding days: {', '.join(max_places3)} = {max_total_days} days"

                # Append data to the list for Criterion 3
                c3_data.append([month, places_str, max_places_str])

                # Print statements for Criterion 3
                print(f"Month: {month}")
                print("Criterion 3:")
                print('------------------------------------------------------------------------------------------------')
                print(places_str)
                print(max_places_str)
                print(' ')

    ###########################################################################################################################################################################

    # Criterion 1
    criteria1_data = pd.DataFrame(c1_data, columns=["Month", "Places meeting Criterion 1", "Maximum Percentage"])
    criteria1_data.to_excel(writer4, sheet_name=f"Criterion_1", index=False)  

    # Criterion 2
    criteria2_data = pd.DataFrame(c2_data, columns=["Month", "Places meeting Criterion 2", "Maximum Average"])
    criteria2_data.to_excel(writer5, sheet_name='Criterion_2', index=False)

    # Criterion 3
    criteria3_data = pd.DataFrame(c3_data, columns=["Month", "Places meeting Criterion 3", "Maximum Total Exceeding Days"])
    criteria3_data.to_excel(writer6, sheet_name='Criterion_3', index=False)


    # Save the Excel writer object
    writer1.save()
    writer2.save()
    writer3.save()
    writer4.save()
    writer5.save()
    writer6.save()

    # pop-up message box with hotspots place names
    show_hotspots(intersection_of_all_criteria, threshold_value, standard_value)


def show_hotspots(intersection_of_all_criteria, threshold_value, standard_value):
    # Convert the set to a string for display
    hotspots_str = "\n".join(intersection_of_all_criteria)
    # Show message box with hotspots
    messagebox.showinfo("Hotspots", f"The hotspots are:\n{hotspots_str}\n\nNote: Applied values below\n\nThreshold Value: {threshold_value}\n\nStandard Value: {standard_value}")


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Process data with custom threshold and standard values")

    # Add arguments for threshold and standard values
    parser.add_argument("standard_value", type=float, help="Standard value")
    parser.add_argument("threshold_value", type=float, help="Threshold value")

    # Parse the arguments
    args = parser.parse_args()

    # Create a Tkinter window
    root = tk.Tk()
    root.title("Data Processing")

    # Create a button to load CSV file
    load_button = tk.Button(root, text="Load CSV", command=load_csv)
    load_button.pack(pady=200, padx=200)

    # Run the Tkinter event loop
    root.mainloop()
    

#### end of code  ####


