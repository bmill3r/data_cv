# Entry Selection and AI Processing

## How Entries Are Scored and Selected

When you run the AI CV Generator, each entry in your CV database is evaluated through this process:

1. **Job Analysis**: The AI first analyzes the job posting to extract:
   - Required skills and technologies
   - Desired experience areas
   - Key responsibilities
   - Industry knowledge requirements
   - Soft skills emphasized

2. **Entry Scoring**: Each CV entry is scored from 0-10 with detailed reasoning:

   ```
   Entry: "Senior Data Scientist at TechCorp"
   Score: 8/10
   Reasoning: "Highly relevant - demonstrates experience with machine learning models 
              and large dataset analysis mentioned in job requirements."
   ```

3. **Improved Descriptions**: If enabled (default), descriptions are enhanced to highlight job-relevant aspects:

   **Original Description:**
   ```
   "Led a team of analysts working on customer segmentation."
   ```

   **Improved Description:**
   ```
   "Led a cross-functional team developing machine learning models for customer 
   segmentation, resulting in 25% improvement in campaign targeting metrics."
   ```

4. **Section-Based Selection**: Entries are filtered by section with customizable limits:

   Example for "experience" section with max_entries=2:
   ```
   1. Data Scientist at AI Company (Score: 9/10) ✓ SELECTED
   2. ML Engineer at Tech Startup (Score: 7/10) ✓ SELECTED
   3. Software Developer at Web Company (Score: 5/10) ✗ NOT SELECTED
   4. IT Support at University (Score: 2/10) ✗ NOT SELECTED (below threshold)
   ```

## Sample API Interaction Walkthrough

The following is a simplified version of what happens during processing:

1. **Job Posting Analysis**: 
   ```
   INPUT: "Looking for a data scientist with Python, SQL, and machine learning experience..."
   OUTPUT: {"required_skills": ["Python", "SQL", "Machine Learning"], ...}
   ```

2. **Professional Summary Generation**:
   ```
   INPUT: Original summary + job requirements
   OUTPUT: "Data scientist with 5+ years of experience in Python and ML model development..."
   ```

3. **Entry Scoring**:
   ```
   INPUT: Entry + job analysis
   OUTPUT: Score: 8/10, Reasoning: "Directly relevant to the required ML experience..."
   ```

4. **Description Improvement**:
   ```
   INPUT: Original description + job requirements
   OUTPUT: Enhanced description highlighting relevant skills
   ```

This process ensures that your CV is automatically customized to emphasize the most relevant qualifications for each specific job posting.

## Important Notes on Path Handling

1. **Use Relative Paths**: Always use relative paths (e.g., `./output`, `./tailored_json`) rather than absolute paths from root (e.g., `/output`) to avoid permission issues.

2. **Output Directory Structure**: The script creates these directories relative to the current working directory:
   ```
   ./output/         - For final PDF/HTML documents
   ./tailored_json/  - For tailored JSON files
   ./logs/           - For logging files
   ./{output-name}_data/ - For CSV files
   ```

3. **Troubleshooting**: If files appear to be missing, check that you're not using absolute paths that might be writing to locations requiring elevated permissions.
