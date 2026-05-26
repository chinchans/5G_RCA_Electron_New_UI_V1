# Use python-jenkins (the correct package)
# Install with: pip install python-jenkins
# Version: 1.8.3 or later (supports Python 3.4+)
import jenkins
from jenkins import JenkinsException
import time
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

def trigger_and_monitor_job(server_url, username, password, job_name):
    """Trigger a Jenkins job and monitor its execution until completion."""
    try:
        # Connect to Jenkins server
        server = jenkins.Jenkins(server_url, username=username, password=password)
        
        # Check if the job exists
        if not server.job_exists(job_name):
            print(f"Error: Job '{job_name}' does not exist.")
            return {"result": None, "console_output": f"Error: Job '{job_name}' does not exist.", "build_number": None}
        
        # Trigger a build for the job
        queue_number = server.build_job(job_name)
        print(f"Build triggered for job '{job_name}', queue number: {queue_number}")
        
        # Wait for the job to start
        queue_item = server.get_queue_item(queue_number)
        while 'executable' not in queue_item:
            print("Waiting for the job to start...")
            time.sleep(2)
            queue_item = server.get_queue_item(queue_number)
        
        # Get build number
        build_number = queue_item['executable']['number']
        print(f"Job started with build number: {build_number}")
        
        # Monitor the build status
        build_info = server.get_build_info(job_name, build_number)
        while build_info['building']:
            print("Job is still running...")
            time.sleep(5)
            build_info = server.get_build_info(job_name, build_number)
        
        # Job completed, fetch result
        result = build_info['result']
        print(f"Job completed with result: {result}")
        
        # Fetch console output from Jenkins using lastCompletedBuild
        console_output = ""
        try:
            # Construct console URL: {jenkins_server_url}/job/{job_name}/lastCompletedBuild/consoleText
            # Remove trailing slash from server_url if present
            server_url_clean = server_url.rstrip('/')
            console_url = f"{server_url_clean}/job/{job_name}/lastCompletedBuild/consoleText"
            
            # Fetch console output using requests with authentication
            response = requests.get(
                console_url,
                auth=HTTPBasicAuth(username, password),
                timeout=30
            )
            
            if response.status_code == 200:
                console_output = response.text
                print(f"Console output fetched successfully from lastCompletedBuild ({len(console_output)} characters)")
            else:
                print(f"Warning: Could not fetch console output. Status code: {response.status_code}")
                console_output = f"Could not fetch console output. Status code: {response.status_code}"
        except Exception as e:
            print(f"Warning: Error fetching console output: {e}")
            console_output = f"Error fetching console output: {str(e)}"
        
        # Return both result and console output
        return {"result": result, "console_output": console_output, "build_number": build_number}
        
    except JenkinsException as e:
        print(f"Jenkins Error: {e}")
        return {"result": None, "console_output": f"Jenkins Error: {e}", "build_number": None}
    except Exception as e:
        print(f"Error: {e}")
        return {"result": None, "console_output": f"Error: {e}", "build_number": None}

def main():
    """Main function to handle test execution with configuration."""
    # Default values (fallback)
    jenkins_server_url = "http://10.138.77.71:8080/"
    jenkins_username = "chandu"
    jenkins_password = "tcs@12345"
    job_name = "GenAI_Phase1_Demo_Script"
    
    # Get configuration from command line arguments
    if len(sys.argv) > 1:
        # First argument is JSON config string
        try:
            config = json.loads(sys.argv[1])
            jenkins_server_url = config.get('jenkins_server_url', jenkins_server_url)
            jenkins_username = config.get('jenkins_username', jenkins_username)
            jenkins_password = config.get('jenkins_password', jenkins_password)
            job_name = config.get('job_name', job_name)
        except json.JSONDecodeError:
            print("Warning: Could not parse config JSON, using defaults")
    
    print(f"Jenkins Server: {jenkins_server_url}")
    print(f"Job Name: {job_name}")
    print(f"Username: {jenkins_username}")
    
    # Trigger and monitor Jenkins job build
    job_result = trigger_and_monitor_job(jenkins_server_url, jenkins_username, jenkins_password, job_name)
    
    # Always ensure job_result is a dict
    if not job_result:
        job_result = {"result": None, "console_output": "Failed to fetch Jenkins job result.", "build_number": None}
    
    result = job_result.get("result")
    console_output = job_result.get("console_output", "")
    build_number = job_result.get("build_number")
    
    # Print console output (this will be captured by subprocess)
    if console_output:
        print("=== JENKINS CONSOLE OUTPUT START ===")
        print(console_output)
        print("=== JENKINS CONSOLE OUTPUT END ===")
    
    # Always print result line (even if None) so backend can extract it
    if result:
        print(f"Job completed with result: {result}")
    else:
        print(f"Job completed with result: FAILED")
        result = "FAILED"
    
    if build_number:
        print(f"Build number: {build_number}")
    
    # Exit with 0 for SUCCESS, 1 for FAILURE/UNSTABLE/etc
    sys.exit(0 if result == "SUCCESS" else 1)

if __name__ == "__main__":
    main()

