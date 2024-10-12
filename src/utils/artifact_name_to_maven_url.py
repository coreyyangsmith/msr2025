def artifact_to_maven_url(artifact_name):
    base_url = "https://mvnrepository.com/artifact"

    # Split the artifact_name into group_id and artifact_id
    group_id, artifact_id = artifact_name.split(":")

    # Create the full Maven URL (without replacing periods with slashes)
    maven_url = f"{base_url}/{group_id}/{artifact_id}"

    return maven_url


artifact_name = "org.apache.druid.extensions:druid-pac4j"
url = artifact_to_maven_url(artifact_name)
print(url)
