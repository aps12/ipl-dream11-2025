# PowerShell script to create deployment package for PythonAnywhere

Write-Host "Creating PythonAnywhere deployment package..." -ForegroundColor Green

# Define the files and folders to include
$files = @(
    "app.py",
    "requirements.txt",
    "update_rankings.py",
    "PYTHONANYWHERE_DEPLOYMENT.md",
    "static",
    "templates",
    "instance"
)

# Output zip file name
$zipFile = "ipl-dream11-deployment.zip"

# Remove old zip if it exists
if (Test-Path $zipFile) {
    Write-Host "Removing old deployment package..." -ForegroundColor Yellow
    Remove-Item $zipFile
}

# Create temporary directory for organizing files
$tempDir = "deployment_temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copying files..." -ForegroundColor Cyan

# Copy files to temp directory
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Gray
        Copy-Item -Path $file -Destination $tempDir -Recurse -Force
    } else {
        Write-Host "  ✗ $file (not found)" -ForegroundColor Red
    }
}

Write-Host "Creating zip file..." -ForegroundColor Cyan

# Create the zip file
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipFile -Force

# Clean up temp directory
Remove-Item -Recurse -Force $tempDir

# Get file size
$size = (Get-Item $zipFile).Length / 1MB
$sizeFormatted = "{0:N2}" -f $size

Write-Host ""
Write-Host "✅ Deployment package created successfully!" -ForegroundColor Green
Write-Host "   File: $zipFile" -ForegroundColor White
Write-Host "   Size: $sizeFormatted MB" -ForegroundColor White
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Read PYTHONANYWHERE_DEPLOYMENT.md for detailed instructions" -ForegroundColor White
Write-Host "   2. Upload $zipFile to PythonAnywhere" -ForegroundColor White
Write-Host "   3. Follow the deployment guide" -ForegroundColor White
Write-Host ""
