#!/usr/bin/env python3

# Spin up a an aws EC2 instance with s3 bucket and monitoring
# Credentials saved in ~/.aws/credentials 

#imports
from boto3 import client
import sys,boto3,requests,shutil,time,webbrowser,subprocess


# globals
ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')
conn = client('s3')

# List of buckets already exists
# I'm using a particular bucket so I can refer to that variable
for bucket in s3.buckets.all():
    bucket = bucket.name
    print("---")

# Create ec2 instance function
def t_create_ec2_instance():
    try:
        instances = ec2.create_instances(
                                     ImageId='ami-0aa7d40eeae50c9a9', #'ami-09d56f8956ab235b3',
                                     MinCount=1,
                                     MaxCount=1,
                                     InstanceType='t2.nano',
                                     UserData="""#!/bin/bash
                                                 yum update
                                                 yum install httpd -y
                                                 systemctl enable httpd
                                                 systemctl start httpd
                                                 yum install -y httpd mariadb-server
                                                 echo "<!DOCTYPE html>
                                                 <html>
                                                 <body>
                                                 <h1>Devops Assignment 1</h1>
                                                 <p> Tibor Molnar </p>
                                                 <p> 20074237 </p>
                                                 <br>
                                                 <img src="https://{code}.s3.amazonaws.com/setu_logo.jpg" > " > /var/www/html/index.html
                                                 echo "<p> This instance is running in availability zone: </p>" >> /var/www/html/index.html
                                                 curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> /var/www/html/index.html
                                                 echo "<p><hr>The instance ID is: </p>" >> /var/www/html/index.html
                                                 curl http://169.254.169.254/latest/meta-data/instance-id >> /var/www/html/index.html
                                                 echo "<hr>The instance type is: " >> /var/www/html/index.html 
                                                 curl http://169.254.169.254/latest/meta-data/instance-type >> /var/www/html/index.html
                                                 echo "</body>
                                                 </html>" >> /var/www/html/index.html""".format(code=bucket),
                                     SecurityGroupIds=['launch-wizard-4'],
                                     KeyName='tmolnar-aws-lab'
                                     )
    except:
        print('Error during Instance Creation')
        # Additional instance queries
    print()
    print('Starting Instance....where ' + 'Instance Id is: ' + instances[0].id)
    instances[0].wait_until_running()
    print('Instance Running.')
    instances[0].reload()
    print('Lets run reload method..')
    ip=instances[0].public_ip_address
    print('Instance Running')
    print('Public Ip address is: ' + ip)
    print('Waiting for website installation............. ')
    time.sleep(40)
    print('Website installation done')
    time.sleep(2)
    print('Opening default website created')
    webbrowser.open_new_tab("http://" + ip)
    # Create a name tag for the instance
    response = ec2.create_tags(
        Resources=[
             instances[0].id,      
        ],
        Tags=[
            {
               'Key': 'Name',
               'Value': 'EC2 devops'
            },
        ]
    )

    # The program should also write both URL's to a file called tmolnarurl.txt
    # the bucket url: "https://{code}.s3.amazonaws.com/setu_logo.jpg"
    # web url: ip
    print('Saving Urls to a file....')
    time.sleep(2)
    f = open("tmolnarurl.txt", "a")
    f.write("bucket url: https://{code}.s3.amazonaws.com/setu_logo.jpg\n")
    f.write("web url: \n" + ip)
    f.close()
    
    print('Copy monitor script to instance, and call it...')
    time.sleep(1)
    # Monitor instance
    # Copy monitor. to the instance, change privilege and start script
    scp_command = 'scp -i tmolnar-aws-lab.pem -o StrictHostKeyChecking=no monitor.sh ec2-user@' + ip + ':/home/ec2-user/' 
    ssh_command = 'ssh -i tmolnar-aws-lab.pem -o StrictHostKeyChecking=no ec2-user@' + ip + " 'chmod 700 monitor.sh'"
    ssh_start_command = 'ssh -i tmolnar-aws-lab.pem -o StrictHostKeyChecking=no ec2-user@' + ip + " './monitor.sh'"
    subprocess.run(scp_command, shell=True)
    print('Copy monitor.sh success!')
    subprocess.run(ssh_command, shell=True)
    print('Connecting to the instance to modify monitor.sh file privilege')
    print('Starting monitor script')
    print('-----------------------')
    subprocess.run(ssh_start_command, shell=True)




# Download SETU logo method
def t_download_file():
    print('Locating Picture for Assignment..............')
    try:
        img_url = 'http://devops.witdemo.net/logo.jpg'
        path = '/home/tmolnar/aws-code/setu_logo.jpg'
        response = requests.get(img_url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
        print('Picture downloaded from: ' + img_url + ' to: ' + path)
    except:
        print('Download faulire')



# S3 Create a Bucket function
def t_create_bucket_and_upload():
    b_name=["tmolnar-test2222"]
    # bucket name can be defined by user but it ruins automation
    # b_name=[str(input('Please input bucket name to be created: '))]


    print('Start Creating bucket....')
    for bucket_name in b_name:   #sys.argv[1:]:
        try:
            response = s3.create_bucket(Bucket=bucket_name)
            print (response)
        except Exception as error:
            print (error)
    time.sleep(5)
    print('Bucket Created')
    print('Bucket name: ' + bucket_name)
    print('Configuring static website.....')

    # Static Website config for Bucket
    website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
    }

    bucket_website = s3.BucketWebsite(bucket_name)   # replace with your bucket name or a string variable
    response = bucket_website.put(WebsiteConfiguration=website_configuration)
    print('Static website configuration done.')

    # Upload file to bucket method
    print('Uploading file................')
    object_name = 'setu_logo.jpg'
    try:
        response = s3.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'))
        print (response)
    except Exception as error:
        print (error)
    time.sleep(2)
    print('Upload Completed.')

    # Test for returning object key
    print('Returning bucket object key as an extra: ')
    for key in conn.list_objects(Bucket=bucket_name)['Contents']:
        print(key['Key'])

    # Public read enable (object_acl = s3.ObjectAcl('bucket_name','object_key'))
    object_acl = s3.ObjectAcl(bucket_name, object_name)
    response = object_acl.put(ACL='public-read')





if __name__ == '__main__':
    t_download_file()
    t_create_bucket_and_upload()
    t_create_ec2_instance()
    
