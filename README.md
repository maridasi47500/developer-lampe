## How to Zip Your Lambda Function

To package your Lambda function, you need to zip the contents of your project directory. Use the following command:
faire  :
```sh
pip install certifi charset_normalizer -t .
pip install ask-sdk-core -t .
pip install colorsys -t .

et
```sh
zip -r my_lambda_function.zip .

# developer-lamp
