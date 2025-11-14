pipeline {
  agent any

  environment {
    TF_DIR = "${env.WORKSPACE}/environments/dev"
    PATH = "$HOME/terraform:$PATH"
  }

  stages {

    stage('Clean Workspace') {
      steps {
        deleteDir()
      }
    }

    stage('Checkout Terraform Project') {
      steps {
        dir("${TF_DIR}") {
          git branch: 'develop', 
              url: 'https://github.com/GeraldOpitz/FUM-TF',
        }
      }
    }

    stage('Terraform Init') {
      steps {
        dir("${TF_DIR}") {
          withAWS(credentials: 'aws-credentials', region: 'us-east-1') {
            sh '''
              echo "Starting Terraform"
              terraform version
              terraform init -reconfigure -backend-config="backend.hcl"
            '''
          }
        }
      }
    }

    stage('Terraform Plan') {
      steps {
        dir("${TF_DIR}") {
          withAWS(credentials: 'aws-credentials', region: 'us-east-1') {
            sh '''
              echo "Planning changes"
              terraform plan -out=tfplan
            '''
          }
        }
      }
    }

    stage('Terraform Apply') {
      when {
        allOf {
          expression { !env.CHANGE_ID }
          anyOf {
            branch 'develop'
            branch 'main'
          }
        }
      }
      steps {
        script {
          input message: "¿Do you wish to apply Terraform changes in ${env.BRANCH_NAME}? Type 'yes' to continue.", ok: "yes"
          dir("${TF_DIR}") {
            withAWS(credentials: 'aws-credentials', region: 'us-east-1') {
              sh '''
                echo "Applying changes"
                terraform apply -auto-approve tfplan
              '''
            }
          }
        }
      }
    }

    stage('Terraform Output') {
      steps {
        dir("${TF_DIR}") {
          withAWS(credentials: 'aws-credentials', region: 'us-east-1') {
            sh '''
              echo "Mostrando Terraform Output:"
              terraform output

              echo "Generando tf-output.json..."
              terraform output -json > tf-output.json
            '''
          }
        }
      }
    }

    stage('Clone Ansible Project') {
      steps {
        dir("${env.WORKSPACE}/ansible") {
          sh 'rm -rf ./* ./.??* || true'
          sh '''
            git clone -b develop \
            https://github.com/GeraldOpitz/Flask-App-User-Manager.git .
          '''
        }
      }
    }

    stage('Generate Test Inventory') {
      when { expression { env.CHANGE_ID } }
      steps {
        script {
          withAWS(credentials: 'aws-credentials', region: 'us-east-1') {
            sh """
              APP_IP=\$(terraform -chdir=$TF_DIR output -raw flask_app_public_ip)
              DB_IP=\$(terraform -chdir=$TF_DIR output -raw flask_db_public_ip)

              cat > ${WORKSPACE}/ansible/ansible/inventories/dev/inventory.ini <<EOF
    [all:vars]
    ansible_user=ubuntu
    ansible_python_interpreter=/usr/bin/python3

    [app]
    APP_EC2 ansible_host=\${APP_IP} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

    [db]
    DB_EC2 ansible_host=\${DB_IP} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    EOF
            """
          }
        }
      }
    }

    stage('Run Ansible - Feature Tests') {
      when {
        expression {
          env.CHANGE_ID &&
          (env.CHANGE_TARGET == 'develop' || env.CHANGE_TARGET == 'main')
        }
      }
      steps {
        script {
          withCredentials([string(credentialsId: 'ansible_vault_pass', variable: 'VAULT_PASS')]) {
            sshagent(['ec2-app-key', 'ec2-db-key']) {
              sh """
                echo "$VAULT_PASS" > ${WORKSPACE}/ansible/.vault_pass.txt
                chmod 600 ${WORKSPACE}/ansible/.vault_pass.txt
                ansible-playbook \
                  -i ${WORKSPACE}/ansible/ansible/inventories/dev/inventory.ini \
                  ${WORKSPACE}/ansible/ansible/playbooks-test.yml \
                  --vault-password-file ${WORKSPACE}/ansible/.vault_pass.txt \
                  -u ubuntu
                rm -f ${WORKSPACE}/ansible/.vault_pass.txt
              """
            }
          }
        }
      }
    }

    stage('Run Ansible - Deploy') {
      when {
        allOf {
          expression { !env.CHANGE_ID }
          anyOf {
            branch 'develop'
            branch 'main'
          }
        }
      }
      steps {
        script {
          withCredentials([string(credentialsId: 'ansible_vault_pass', variable: 'VAULT_PASS')]) {
            sshagent(['ec2-app-key', 'ec2-db-key']) {
              sh """
                echo "$VAULT_PASS" > ${WORKSPACE}/ansible/.vault_pass.txt
                chmod 600 ${WORKSPACE}/ansible/.vault_pass.txt
                ansible-playbook \
                  -i ${WORKSPACE}/ansible/ansible/inventories/dev/inventory.ini \
                  ${WORKSPACE}/ansible/ansible/playbooks.yml \
                  --vault-password-file ${WORKSPACE}/ansible/.vault_pass.txt \
                  -u ubuntu
                rm -f ${WORKSPACE}/ansible/.vault_pass.txt
              """
            }
          }
        }
      }
    }

  }

  post {
    success {
      echo "Resources created and configured with Ansible."
    }
    failure {
      echo "Failed to create or configure resources."
    }
  }
}
