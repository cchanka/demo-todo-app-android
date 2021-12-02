import os, sys, requests
import unittest
import xml.etree.ElementTree as ET
from junitparser import JUnitXml, Failure
from github import Github
from datetime import timedelta, date
import pandas as pd


######## GITHUB ########
# Initialize Github
def init_github():
    global github_repo
    # Get Github token and repo slug from environment variables
    token = os.getenv('GITHUB_TOKEN')
    github_repo_slug = os.getenv('GITHUB_REPO_SLUG')

    # Create github object
    github = Github(token)
    # Create github repo object
    github_repo = github.get_repo(github_repo_slug)

# PR comment posting
def github_pr_comment_post(pr_id, pr_comment):
    init_github()
    # Create github issue object from repo
    issue = github_repo.get_issue(int(pr_id))
    # Create a comment in the Github issue
    issue.create_comment(pr_comment)
    print("Posted to Github PR.")
    return

# Get test cases count
def get_kpi_test_cases():
    pat = os.getenv('PAT')
    organization = os.getenv('AZDO_ORG')
    project = os.getenv('AZDO_PROJ')
    buildUri = os.getenv('BUILD_URI')
    # testQueryEndpoint = "https://:{0}@dev.azure.com/{1}/{2}/_apis/test/runs?minLastUpdatedDate=2021-11-10&maxLastUpdatedDate=2021-11-12&buildIds={3}&api-version=6.0".format(
            # pat,
            # organization,
            # project,
            # build_id)
    testRunListEndpoint = "https://:{pat}@dev.azure.com/{org}/{proj}/_apis/test/runs?buildUri={buildUri}&api-version=6.0".format(
            pat=pat,
            org=organization,
            proj=project,
            buildUri=buildUri)
    testRunListResponse = requests.get(url=testRunListEndpoint)
    testRunId = testRunListResponse.json()['value'][0]['id']

    testRunByIdEndpoint = "https://:{pat}@dev.azure.com/{org}/{proj}/_apis/test/runs/{testRun}".format(
            pat=pat,
            org=organization,
            proj=project,
            testRun=testRunId)

    testRunByIdResponse = requests.get(url=testRunByIdEndpoint)
    totalTests = testRunByIdResponse.json()['totalTests']
    incompleteTests = testRunByIdResponse.json()['incompleteTests']
    notApplicableTests = testRunByIdResponse.json()['notApplicableTests']
    passedTests = testRunByIdResponse.json()['passedTests']
    unanalyzedTests = testRunByIdResponse.json()['unanalyzedTests']

    print("Total Tests : {0}".format(totalTests))
    print("Incomplete Tests : {0}".format(incompleteTests))
    print("N/A Tests : {0}".format(notApplicableTests))
    print("Passed Tests : {0}".format(passedTests))
    print("Unanalyzed Tests : {0}".format(unanalyzedTests))
    return

# Get average build time last month
def get_kpi_build_time_average():
    pat = os.getenv('PAT')
    organization = os.getenv('AZDO_ORG')
    project = os.getenv('AZDO_PROJ')
    buildDefinition = os.getenv('BUILD_DEF')
    lastMonthDate = date.today() - timedelta(days=30)
    testRunListEndpoint = "https://:{pat}@dev.azure.com/{org}/{proj}/_apis/build/builds?definitions={buildDef}&minTime={minTime}&api-version=6.0".format(
            pat=pat,
            org=organization,
            proj=project,
            buildDef=buildDefinition,
            minTime=lastMonthDate)
    testRunListResponse = requests.get(url=testRunListEndpoint)
    totalBuildTimeInSec=0.0
    builds=testRunListResponse.json()['value']
    buildCount=len(builds)
    for build in builds:
        startTime = pd.to_datetime(build['startTime'], format='%Y-%m-%dT%H:%M:%S.%fZ')
        finishTime = pd.to_datetime(build['finishTime'], format='%Y-%m-%dT%H:%M:%S.%fZ')
        timeTaken = finishTime - startTime
        totalBuildTimeInSec += timeTaken.total_seconds()
    
    averageBuildTimeInSec = totalBuildTimeInSec / buildCount
    print("Average Build Time (last 30 days):", timedelta(seconds=averageBuildTimeInSec))

    return

# Get pipeline runs count last month
def get_kpi_pipeline_runs_count(buildDef):
    if not isinstance(buildDef, int):
        raise TypeError("The Build Definition can only be int")
    
    pat = os.getenv('PAT')
    organization = os.getenv('AZDO_ORG')
    project = os.getenv('AZDO_PROJ')
    buildDefinition = buildDef
    lastMonthDate = date.today() - timedelta(days=30)
    # buildMetricsEndpoint = "https://:{pat}@dev.azure.com/{org}/{proj}/_apis/build/definitions/{buildDef}/metrics/daily?minMetricsTime={minTime}&api-version=6.0-preview.1".format(
    buildMetricsEndpoint = "https://:{pat}@dev.azure.com/{org}/{proj}/_apis/build/builds?definitions={buildDef}&minTime={minTime}&api-version=6.0".format(
            pat=pat,
            org=organization,
            proj=project,
            buildDef=buildDefinition,
            minTime=lastMonthDate)
    buildMetricsResponse = requests.get(url=buildMetricsEndpoint)

    print("Total Pipeline Runs Last Month:", buildMetricsResponse.json()['count'])

    return

# Posting Jacoco report summary as a PR Comment
def github_pr_comment_jacoco_sum_post(pr_id, jacoco_xml_path):
    total_covered = 0
    total_missed = 0

    # Fetch jacoco summary dictionary from the jacoco xml report
    jacoco_summary = jacoco_xml_summary_parse(jacoco_xml_path)
    pr_comment = "Test Coverage Summary: <br>"
    # Iterate through coverage types
    for coverage_type in jacoco_summary.keys():
        # Fetch values and update totals
        covered = int(jacoco_summary[coverage_type]["covered"])
        total_covered += covered
        missed = int(jacoco_summary[coverage_type]["missed"])
        total_missed += missed
        coverage = float((covered) / (covered + missed) * 100)

        pr_comment += "- {0} (coverage {1:.2f}%): covered - {2} | missed - {3} <br>".format(
            coverage_type,
            coverage,
            covered,
            missed
        )
    # Calculate total coverage
    total_coverage = float((total_covered) / (total_covered + total_missed) * 100)
    pr_comment += "{0} (coverage {1:.2f}%): covered - {2} | missed - {3}".format(
        "Total",
        total_coverage,
        total_covered,
        total_missed
    )
    # Post PR comment to github
    github_pr_comment_post(pr_id=pr_id, pr_comment=pr_comment)

######## SLACK ########
# Initialize Slack
def init_slack():
    global slack_webhook_url
    # Get Slack webhook url from enviroment variables
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')


def slack_msg_post(slack_message):
    init_slack()
    payload = '{"text":"%s"}' % slack_message
    # Post data to Slack channel
    response = requests.post(slack_webhook_url, data=payload)
    print("Posted to Slack.")
    print(response.text)
    return

def slack_msg_post_failed_tests(pr_id, test_result_directory):
    init_slack()

    slack_msg="*PR ID: %s - Tests Failed *\n" % pr_id
    junitTestResults=junit_xml_dir_parse(test_result_directory)
    # print("--", junitTestResults)
    for test in junitTestResults.keys():
        slack_msg+="Test - *%s*\n" % test
        slack_msg+="Classname - *%s*\n" % junitTestResults[test]['classname']
        slack_msg+="Error Msg :\n```%s```\n\n" % junitTestResults[test]['message']

    payload = '{"text":"%s"}' % slack_msg
    # Post data to Slack channel
    response = requests.post(slack_webhook_url, data=payload)
    print("Posted to Slack.")
    return

######## JACOCO ########
# Parse Jacoco XML report
def jacoco_xml_summary_parse(reportPath):
    # Parse xml
    tree = ET.parse(reportPath)
    root = tree.getroot()
    summary = {}
    # Iterate through top level 'counter' nodes
    for child in root.findall("./counter"):
        # Add to summary dictionary
        summary[child.attrib["type"]] = {
            "missed": child.attrib["missed"], "covered": child.attrib["covered"]}
    
    return summary

######## JUnit ########
# Parse JUnit XML report
def junit_xml_dir_parse(reportDirPath):
    # Parse xml
    failedTests = {}
    directory = os.fsencode(reportDirPath)
    
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".xml"): 
            suite = JUnitXml.fromfile(os.path.join(reportDirPath, filename))
            for case in suite:
                # print(case)
                if case.result:
                    # print(case.result[0])
                    if isinstance(case.result, Failure):
                        testCase={}
                        testCase['classname']=case.classname
                        testCase['message']=case.result.message
                        testCase['status']="FAILED"
                        failedTests[case.name]=testCase
    
    return failedTests

######## main ########
def main():
    script = sys.argv[0]
    resource = sys.argv[1]
    action = sys.argv[2]
    payload = sys.argv[3:]

    if resource == "github-pr-comment":
        if action == "post":
            github_pr_comment_post(pr_id=payload[0], pr_comment=payload[1])

    if resource == "github-pr-comment-jacoco-summary":
        if action == "post":
            github_pr_comment_jacoco_sum_post(pr_id=payload[0], jacoco_xml_path=payload[1])

    if resource == "slack-msg":
        if action == "post":
            slack_msg_post(slack_message=payload[0])

    if resource == "slack-msg-failed-tests":
        if action == "post":
            slack_msg_post_failed_tests(pr_id=payload[0], test_result_directory=payload[1])

    if resource == "kpi-test-cases":
        if action == "get":
            get_kpi_test_cases()
    
    if resource == "kpi-build-time-average":
        if action == "get":
            get_kpi_build_time_average()
    
    if resource == "kpi-pipeline-runs-count-last-month":
        if action == "get":
            get_kpi_pipeline_runs_count(buildDef=int(payload[0]))


if __name__ == "__main__":
    main()
