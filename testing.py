import json
import pandas as pd
import re

def load_json_tasks(json_file):
    """Load tasks from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def load_excel_tasks(excel_file):
    """Load tasks from Excel file."""
    # Skip rows that are empty or just section headers
    df = pd.read_csv(excel_file)
    return df[['Task', 'Description', 'Skill', 'Other reqs']].fillna('')

def clean_text(text):
    """Clean text for better matching."""
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower().strip())

def find_matching_task(excel_task, json_tasks):
    """Find matching JSON task for Excel task."""
    excel_task_clean = clean_text(excel_task)
    
    # Try exact name match first
    for task in json_tasks:
        if clean_text(task['name']) == excel_task_clean:
            return task
    
    # Try description match if no exact name match
    for task in json_tasks:
        if excel_task_clean in clean_text(task['description']):
            return task
    
    return None

def generate_new_task(task_name, description, skill, other_reqs, sort_id):
    """Generate a new task entry for tasks only in Excel."""
    return {
        "id": f"NEW_{sort_id}",
        "name": task_name,
        "description": description if description else task_name,
        "clientSortId": str(sort_id),
        "skills": [{"skill": s.strip(), "level": "1"} for s in skill.split(',') if s.strip()],
        "other": other_reqs,
        "tier": "Easy",  # Default tier
        "area": "General",  # Default area
        "worldPosition": {"x": 0, "y": 0, "z": 0},
        "requiredItems": [],
        "NPC": None
    }

def process_tasks(json_file, excel_file, output_file):
    """Main processing function."""
    json_tasks = load_json_tasks(json_file)
    excel_df = load_excel_tasks(excel_file)
    
    updated_tasks = []
    current_sort_id = 1
    
    for _, row in excel_df.iterrows():
        task_name = row['Task']
        
        # Skip empty rows
        if not task_name:
            continue
            
        # Check if this is a section header
        if ':' in task_name or 'Pt.' in task_name:
            # Add section header as a task
            updated_tasks.append(generate_new_task(
                task_name,
                "Section Header",
                "",
                "",
                current_sort_id
            ))
        else:
            # Find matching task in JSON
            matching_task = find_matching_task(task_name, json_tasks)
            
            if matching_task:
                # Update existing task
                matching_task = matching_task.copy()
                matching_task['clientSortId'] = str(current_sort_id)
                if row['Description']:
                    matching_task['description'] = row['Description']
                if row['Other reqs']:
                    matching_task['other'] = row['Other reqs']
                updated_tasks.append(matching_task)
            else:
                # Create new task
                updated_tasks.append(generate_new_task(
                    task_name,
                    row['Description'],
                    row['Skill'],
                    row['Other reqs'],
                    current_sort_id
                ))
        
        current_sort_id += 1
    
    # Write updated tasks to file
    with open(output_file, 'w') as f:
        json.dump(updated_tasks, f, indent=2)
    
    return updated_tasks

def print_task_summary(tasks):
    """Print summary of task processing."""
    print(f"\nProcessed {len(tasks)} tasks:")
    new_tasks = sum(1 for task in tasks if task['id'].startswith('NEW_'))
    print(f"- {new_tasks} new tasks created")
    print(f"- {len(tasks) - new_tasks} existing tasks updated")
    
    # Print first few tasks as example
    print("\nExample of first few tasks:")
    for task in tasks[:5]:
        print(f"\nTask: {task['name']}")
        print(f"Sort ID: {task['clientSortId']}")
        print(f"ID: {task['id']}")

if __name__ == "__main__":
    # File paths
    json_file = "json/min/league5_tasks.min.json"
    excel_file = "leagues.csv"
    output_file = "updated_league_tasks.json"
    
    try:
        updated_tasks = process_tasks(json_file, excel_file, output_file)
        print_task_summary(updated_tasks)
        print(f"\nUpdated tasks have been saved to {output_file}")
    except Exception as e:
        print(f"Error processing tasks: {str(e)}")