 
# Useful docs

 https://repost.aws/questions/QU14iutbqtSsm1gHwQwt02pA/upgrade-to-python-3-9-on-cloud-9
 
 https://repost.aws/knowledge-center/lambda-import-module-error-python
 

# Create a Lambda Layers:

```
mkdir python
cd python
python -m pip install requests "urllib3<2" --target ./
cd ..
zip -r my_layer.zip python
aws lambda publish-layer-version --layer-name pandas --zip-file fileb://my_layer.zip --compatible-runtimes python3.7 python3.8
```