import csv

# Departments to exclude
department_enum = {
    "Art and Design",
    "Business and Economics",
    "Communication Arts",
    "Computer Technology and Information Systems",
    "Counseling",
    "Criminal Justice",
    "Educational Foundations and Leadership",
    "Health, Human Performance, and Sport",
    "History, Politics, and Geography",
    "Language and Literature",
    "Life Sciences",
    "Music",
    "Physical Sciences and Mathematics",
    "Psychology and Sociology",
    "Technology and Applied Science",
}

# Input and output CSV file paths
input_file = 'faculty_directory.csv'
output_file = 'filtered_output.csv'

# Read input CSV and filter rows
with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    # Filter rows where the department is not in the department_enum
    filtered_rows = [
        row for row in reader if row['Department'] in department_enum
    ]

# Write filtered rows to the output CSV
with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_rows)

print(f"Filtered data has been saved to {output_file}.")
