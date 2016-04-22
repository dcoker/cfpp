.. image:: https://img.shields.io/pypi/v/cfpp.svg?maxAge=600   :target:

====
cfpp
====

What is cfpp?
-------------

cfpp is a pre-processor for CloudFormation templates which adds additional
functions to the JSON language.

AWS CloudFormation provides several built-in functions that help you define
your stacks. These "intrinsic" functions assign runtime values to properties.
For example, the ``Ref`` function can refer to the value of Parameters or the
ARNs of Resources created by the stack.

While the intrinsic functions allow users to access runtime variables, the core
CloudFormation language does not have many affordances for common devops tasks.
The lack of support for injecting or reusing content, combined with the poor
usability of editing large JSON documents, can result in users looking towards
unnecessarily complex solutions to accomplish common tasks.

cfpp adds "extrinsic" functions to CloudFormation templates. These extrinsic
functions allow you to inject content into a CloudFormation template before it
is passed to the CloudFormation API for processing. The output of cfpp is
stable-sorted, and suitable for committing to version control and for human
diffing. All extrinsic functions are evaluated before emitting the processed
CloudFormation.

Functions
---------

Here are some of the functions that are implemented:

``CFPP::FileToString``
    Reads a file and injects its content into the template as a string, with
    leading and trailing whitespace removed.

    Example:

    ::

          "Description": {
            "CFPP::FileToString": "DESCRIPTION.txt"
          }

``CFPP::FileToStringRaw``
    Reads a file and injects its content into the template as a string.

    Example:

    ::

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

    Example:

    ::

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

    Example:

    ::

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

    Example:

    ::

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

    Example:

    ::

        "KeyName": {
            "Description": "SSH public key to install on the cluster.",
            "Type": "AWS::EC2::KeyPair::KeyName"
            "Default": {"CFPP::Trim": {"CFPP::Command": ["/usr/bin/id", "-un"]}}
        },

Note that extrinsic functions can be composed. Example:

::

    { "CFPP::StringSplit": ["\n", { "CFPP::FileToString": "urls.txt" } ] }

Installing
----------

::

    pip install cfpp

Example Usage
-------------

Procedurally:

::

    $ cfpp stack.template > stack.json
    $ aws cloudformation create-stack --stack-name my-stack --template-body file://./stack.json


Using bash process-redirection:

::

    $ aws cloudformation create-stack --stack-name my-stack --template-body file://./<(cfpp stack.template)

Limitations
-----------

Extrinsic functions cannot read runtime properties, Parameters, Mappings, Conditions, or Outputs.
