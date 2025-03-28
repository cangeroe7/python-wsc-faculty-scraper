import csv

def load_names(file_path):
    with open(file_path, mode='r', newline='') as file:
        reader = csv.reader(file)
        return [row[0] for row in reader]  # Only take the first column (name)

def compare_names(file1, file2):
    names1 = load_names(file1)
    names2 = load_names(file2)
    
    matches = 0
    unmatched_names = []

    # Check for names in file1 that are not in file2
    for name in names1:
        if name in names2:
            matches += 1
        else:
            unmatched_names.append((name, 'file1'))

    # Check for names in file2 that are not in file1
    for name in names2:
        if name not in names1:
            unmatched_names.append((name, 'file2'))

    # Print unmatched names and tally
    for name, file in unmatched_names:
        print(f"Name '{name}' is only in {file}")

    print(f"\nTotal matches found: {matches}")

if __name__ == "__main__":
    file1 = './faculty_directory.csv'  # Path to the first CSV file
    file2 = './faculty_directory_bak.csv'  # Path to the second CSV file
    compare_names(file1, file2)
