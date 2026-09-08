$pubspec = "mobile/pubspec.yaml"

$content = Get-Content $pubspec

$versionLine = $content | Where-Object {
    $_ -match "^version:"
}

$currentVersion = ($versionLine -replace "^version:\s*", "").Trim()

$parts = $currentVersion.Split("+")
$versionName = $parts[0]
$buildNumber = $parts[1]

$versionParts = $versionName.Split(".")

$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]
$patch = [int]$versionParts[2]

$patch++

$newVersion = "$major.$minor.$patch+$buildNumber"

$content = $content -replace "^version:.*", "version: $newVersion"

Set-Content $pubspec $content

Write-Host "App version: $currentVersion -> $newVersion"

git add $pubspec

git commit -m "Bump app version to $newVersion"

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

git -c alias.push= push @args

exit $LASTEXITCODE