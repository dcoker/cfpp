.. image:: https://img.shields.io/pypi/v/cfpp.svg?maxAge=600   :target:

====
cfpp
====

-------------
What is cfpp?
-------------

cfpp is a pre-processor for CloudFormation templates which adds additional
functions to the CloudFormation language.

AWS CloudFormation provides several built-in functions that help you define
your stacks. These "intrinsic" functions assign runtime values to properties.
For example, the ``Ref`` function can refer to the value of Parameters or the
ARNs of Resources created by the stack.

While the intrinsic functions allow users to access runtime variables, the core
CloudFormation language does not have many affordances for common devops tasks
that happen before the template is submitted for evaluation. cfpp addresses
this gap by adding "extrinsic" functions to the language. These extrinsic
functions allow you to inject content into a CloudFormation template before it
is passed to the CloudFormation API for processing. The output of cfpp is
stable-sorted, suitable for committing to version control, and informative
when diffing. All extrinsic functions are evaluated before emitting the processed
CloudFormation.

Here are some tasks that the extrinsic functions can simplify:

- Re-use of configuration information between templates (ex: mappings, conditions, outputs).

- Injection of information from the configuration environment (ex: files, user's login ID).

- Injection of JSON files directly into the JSON template, or as properly escaped strings.

- Deploying single-file Lambda functions without the need to write the package a zip file on S3.

- Composing MIME multipart strings for use with ``UserData`` and ``cloud-init``.

---------
Functions
---------

Here are some of the functions that are implemented:

``CFPP::FileToString``
    Reads a file and injects its content into the template as a string, with
    leading and trailing whitespace removed.

    Example::

          "Description": {
            "CFPP::FileToString": "DESCRIPTION.txt"
          }

``CFPP::FileToStringRaw``
    Reads a file and injects its content into the template as a string.

    Example::

        "files" : {
          "/etc/mysql/my.cnf" : {
            "content" : { "CFPP::FileToStringRaw": "my.cnf" },
            "mode"  : "000644",
            "owner" : "root",
            "group" : "root"
          }
        }

``CFPP::JsonFileToString``
    Parses a local JSON file and re-serializes it to a string.

    Example::

        "files": {
          "/opt/app/config/config.yaml": {
            "content": {
              "Fn::Join": [
                "",
                [
                  "mappings: ",
                  { "CFFP::JsonFileToString": "mappings.json" },
                  ...

``CFPP::JsonFile``
    Reads a JSON file and injects its content in its JSON form.

    Example::

        "WebserverInstanceType": {
          "Description": "The machine type of the frontend instance.",
          "Type": "String",
          "AllowedValues": {
            "CFPP::JsonFile": "sample_sriov_instance_types.json"
          }
        }

``CFPP::MimeMultipart``
    Compose a multipart MIME message from a list of component MIME types and payloads. This is useful for
    ``UserData`` properties.

    Example::

        "UserData": {
          "Fn::Base64": {
            "CFPP::MimeMultipart": [
              [
                "text/x-shellscript",
                {
                  "CFPP::FileToString": "sample_userdata.sh"
                }
              ],
              [
                "text/cloud-config",
                {
                  "CFPP::FileToString": "cloud-config.yaml"
                }
              ]
            ]
          }
        }

``CFPP::StringSplit``
    Given a string, split it with a chosen delimiter and inject it as a JSON array.

``CFPP::Trim``
    Given a string, strip leading and trailing whitespace.

``CFPP::Command``
    Executes a subprocess and injects its output into the template as a string.

    Example::

        "KeyName": {
            "Description": "SSH public key to install on the cluster.",
            "Type": "AWS::EC2::KeyPair::KeyName"
            "Default": {"CFPP::Trim": {"CFPP::Command": ["/usr/bin/id", "-un"]}}
        }

``CFPP::Kms::EncryptFile``
    Encrypts a small file (< 4KB) using a KMS key.

    The first parameter must be a KMS KeyID that can be resolved by the AWS API (examples:
    full key ARN, or strings prefixed by alias/ or key/). The second parameter is the name
    of the file to encrypt. The third parameter is optional, and if present, is passed verbatim
    as the EncryptionContext.

    The returned ciphertext is base64 encoded binary data. Applications can pass the decoded
    ciphertext to
    `KMS Decrypt <http://docs.aws.amazon.com/kms/latest/APIReference/API_Decrypt.html>`
    as ``CiphertextBlob`` to recover the plaintext value. Note that the receiving process
    must be granted permission to decrypt the value using IAM Policies, KMS Key Policies,
    or KMS Grants.

    Example::

        "files": {
          "/opt/app/config/config.yaml": {
            "content": {
              "Fn::Join": [
                "",
                [
                  "slack_api_key: ",
                  { "CFFP::Kms::EncryptFile": [ "alias/production", "slack-api-key.txt" },
                  ...


-----------------
Nested Extrinsics
-----------------

Note that extrinsic functions can be composed. Example::

    { "CFPP::StringSplit": ["\n", { "CFPP::FileToString": "urls.txt" } ] }

----------
Installing
----------

::

    pip install cfpp

--------------------
Example: Basic Usage
--------------------

Rendering the template to a JSON file::

    $ cfpp stack.template > stack.json
    $ aws cloudformation create-stack \
        --stack-name my-stack \
        --template-body file://./stack.json

Rendering the template using bash process-redirection::

    $ aws cloudformation create-stack \
        --stack-name my-stack \
        --template-body file://<(cfpp stack.template)

------------------------
Example: Lambda Function
------------------------

Lambda function code can be embedded in CloudFormation templates, and the
``{"CFPP::FileToString"}`` method can be used to inject a file directly
into the template. See the ``examples`` directory for a complete example.

Excerpt::

    "WordCountLambdaFunction": {
      "Type": "AWS::Lambda::Function",
      "Properties": {
        "Handler": "index.handler",
        "Role": {
          "Fn::GetAtt": [
            "LambdaExecutionRole",
            "Arn"
          ]
        },
        "Code": {
          "ZipFile": {
            "CFPP::FileToString": "func.py"
          }
        },
        "Runtime": "python2.7",
        "Timeout": "30"
      }
    }

You can then manage your entire function lifecycle using the
standard ``aws cloudformation`` command line tools. Example::

    $ STACK_NAME=s-$(date +%s)
    $ aws cloudformation validate-template \
        --template-body file://<(cfpp -s lambda lambda/lambda.template)
    $ aws cloudformation create-stack --stack-name ${STACK_NAME} \
        --template-body file://<(cfpp -s lambda lambda/lambda.template) \
        --capabilities CAPABILITY_IAM
    $ aws cloudformation update-stack --stack-name ${STACK_NAME} \
        --template-body file://<(cfpp -s lambda lambda/lambda.template) \
        --capabilities CAPABILITY_IAM
    $ aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME}
    $ FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --query 'Stacks[].Outputs[?OutputKey==`FunctionName`].OutputValue' \
        --output text)
    $ aws lambda invoke --function-name ${FUNCTION_NAME} \
        --payload '{"URL": "s3://..."}' \
        /dev/stdout

-----------
Limitations
-----------

Extrinsic functions cannot read runtime properties, Parameters, Mappings, Conditions, or Outputs.
