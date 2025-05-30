pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'SonarQube'
        SONAR_AUTH_TOKEN = credentials('sonarqube-token')
        PATH = "/opt/sonar-scanner/bin:${env.PATH}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv("${SONARQUBE_SERVER}") {
                    sh '''
                        /opt/sonar-scanner/bin/sonar-scanner \
                        -Dsonar.projectKey=APB2TAL \
                        -Dsonar.sources=. \
                        -Dsonar.php.version=8.0 \
                        -Dsonar.host.url=http://10.30.212.36:9000/ \
                        -Dsonar.login=${SONAR_AUTH_TOKEN} \
                        -Dsonar.python.version=3.x
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

stage('Deploy to Web Server') {
    steps {
        sshagent(['webserver_ssh_credentials_id']) {
            sh '''
                echo "Verificando clave SSH"
                ssh-add -l

                ssh -o StrictHostKeyChecking=no root@10.30.212.36 <<EOF
set -e

echo "=== INICIANDO DESPLIEGUE EN SERVIDOR REMOTO ==="

git config --global --add safe.directory /var/www/APB2TAL

if [ -d /var/www/APB2TAL ]; then
    echo "Repositorio ya existente, actualizando..."
    cd /var/www/APB2TAL
    git reset --hard HEAD
    git pull
else
    echo "Clonando repositorio..."
    git clone https://github.com/AlbertXicola/APB2TAL.git /var/www/APB2TAL
fi

cd /var/www/APB2TAL

if [ ! -d "env" ]; then
    echo "Creando entorno virtual..."
    python3.10 -m venv env
fi

source env/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt

python manage.py migrate

echo "Verificando si el puerto 80 está en uso..."
PID=$(sudo lsof -t -i :80)
if [ -n "$PID" ]; then
    echo "Matando proceso en el puerto 80 (PID $PID)"
    sudo kill -9 $PID
else
    echo "Puerto 80 libre."
fi

echo "Levantando servidor..."
nohup python3 manage.py runserver 0.0.0.0:80 > /var/www/server.log 2>&1 &

echo "=== DESPLIEGUE COMPLETADO ==="
EOF
            '''
        }
    }
}


        stage('DAST con OWASP ZAP') {
            steps {
                script {
                    sh 'docker rm -f zap_scan || true'

                    sh '''
                        docker run --user root --name zap_scan -v zap_volume:/zap/wrk/ -t ghcr.io/zaproxy/zaproxy:stable \
                        zap-baseline.py -t http://10.30.212.36 \
                        -r reporte_zap.html -I
                    '''

                    sh 'docker cp zap_scan:/zap/wrk/reporte_zap.html ./reporte_zap.html'
                    sh 'docker rm zap_scan'
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reporte_zap.html', fingerprint: true
                }
            }
        }
    }
}
