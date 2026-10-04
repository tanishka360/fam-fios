<#
.SYNOPSIS
    Automated AWS Cloud Deployment Script for FAM-FIOS (Amazon ECR & AWS App Runner / ECS).

.DESCRIPTION
    Builds the production Docker container, authenticates with Amazon Elastic Container Registry (ECR),
    creates the repository if missing, tags the image, and pushes it for zero-downtime deployment.

.EXAMPLE
    .\deploy_aws.ps1 -AwsAccountId "123456789012" -Region "ap-south-1"
#>

param (
    [Parameter(Mandatory = $false)]
    [string]$AwsAccountId = "",

    [Parameter(Mandatory = $false)]
    [string]$Region = "ap-south-1",

    [Parameter(Mandatory = $false)]
    [string]$RepoName = "fam-fios",

    [Parameter(Mandatory = $false)]
    [string]$ImageTag = "latest"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  FAM-FIOS: Automated AWS Cloud Container Deployment      " -ForegroundColor Cyan
Write-Host "  Patent Invention: 24BIT0370-24BIT0390-IDF-01            " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verify AWS CLI
Write-Host "🔍 [1/5] Verifying AWS CLI installation..." -ForegroundColor Yellow
$awsCmd = Get-Command "aws" -ErrorAction SilentlyContinue
if (-not $awsCmd) {
    Write-Host "❌ Error: AWS CLI ('aws') is not installed or not in PATH." -ForegroundColor Red
    Write-Host "   Install AWS CLI from: https://aws.amazon.com/cli/" -ForegroundColor Gray
    Exit 1
}
Write-Host "   ✅ AWS CLI found." -ForegroundColor Green

# 2. Resolve AWS Account ID if not passed
if (-not $AwsAccountId) {
    Write-Host "🔍 [2/5] Fetching caller identity from active AWS credentials..." -ForegroundColor Yellow
    try {
        $identityJson = aws sts get-caller-identity --output json | ConvertFrom-Json
        $AwsAccountId = $identityJson.Account
        Write-Host "   ✅ Detected AWS Account ID: $AwsAccountId" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error: Could not determine AWS Account ID. Please run 'aws configure' or pass -AwsAccountId." -ForegroundColor Red
        Exit 1
    }
} else {
    Write-Host "   ✅ Using provided AWS Account ID: $AwsAccountId" -ForegroundColor Green
}

$EcrRegistry = "$AwsAccountId.dkr.ecr.$Region.amazonaws.com"
$FullImageUri = "$EcrRegistry/${RepoName}:${ImageTag}"

# 3. Authenticate Docker with Amazon ECR
Write-Host "🔐 [3/5] Authenticating Docker with Amazon ECR ($Region)..." -ForegroundColor Yellow
try {
    aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $EcrRegistry
    Write-Host "   ✅ Docker successfully authenticated with ECR." -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: Docker ECR login failed. Ensure Docker Desktop is running and AWS permissions allow 'ecr:GetAuthorizationToken'." -ForegroundColor Red
    Exit 1
}

# 4. Check or Create ECR Repository
Write-Host "📦 [4/5] Checking Amazon ECR repository '$RepoName'..." -ForegroundColor Yellow
$repoCheck = aws ecr describe-repositories --repository-names $RepoName --region $Region 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Creating new Amazon ECR repository '$RepoName'..." -ForegroundColor Gray
    aws ecr create-repository --repository-name $RepoName --region $Region --image-scanning-configuration scanOnPush=true | Out-Null
    Write-Host "   ✅ Repository '$RepoName' created with automatic vulnerability scanning enabled." -ForegroundColor Green
} else {
    Write-Host "   ✅ Repository '$RepoName' already exists." -ForegroundColor Green
}

# 5. Build, Tag, and Push Container Image
Write-Host "🚀 [5/5] Building & Pushing Docker image to Amazon ECR..." -ForegroundColor Yellow
Write-Host "   Image URI: $FullImageUri" -ForegroundColor Cyan

docker build -t ${RepoName}:${ImageTag} .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Docker build failed." -ForegroundColor Red
    Exit 1
}

docker tag ${RepoName}:${ImageTag} $FullImageUri
docker push $FullImageUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Docker push to ECR failed." -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  🎉 SUCCESS! Container Image Pushed to Amazon ECR         " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Image URI: $FullImageUri" -ForegroundColor White
Write-Host ""
Write-Host "👉 Next Step: Deploy to AWS App Runner for a live HTTPS URL:" -ForegroundColor Yellow
Write-Host "   1. Open the AWS Console -> App Runner -> 'Create an App Runner service'"
Write-Host "   2. Choose 'Container registry' -> 'Amazon ECR'"
Write-Host "   3. Select Image URI: $FullImageUri"
Write-Host "   4. Set Port: 8501, vCPU: 1 vCPU, Memory: 2 GB"
Write-Host "   5. Click 'Deploy' — AWS will provision your live public HTTPS address!" -ForegroundColor Cyan
Write-Host ""
