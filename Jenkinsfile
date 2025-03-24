pipeline {
    agent any

    environment {
        AWS_REGION = "ap-northeast-2"
        ECR_REPO = "941377153895.dkr.ecr.ap-northeast-2.amazonaws.com/oops/ai"
        EC2_USER = "ubuntu"
        EC2_HOST = "10.0.5.248"  // Airflow있는 EC2 프라이빗 IP 
        TAG = "${BUILD_NUMBER}" // Jenkins 빌드 번호를 태그로 사용 
	WORKSPACE = "/var/lib/jenkins/workspace/AI"
	REPO_URL = "https://github.com/profect-Oops/AI-repo.git"
	BRANCH = "main"
    }

    stages {
        stage('Checkout Code') {
            steps {
                   sh '''
                    # 기존 폴더 삭제 (기존 데이터가 남아 있으면 문제 발생 가능)
                    rm -rf AI-repo

                    # --no-checkout: 아직 체크아웃 안 함
                    # --depth 1: 커밋 히스토리 없이 최신 코드만 가져옴
                    # --filter=tree:0: 필요 없는 폴더는 다운로드하지 않음
                    git clone --no-checkout --depth 1 --filter=tree:0 ${REPO_URL} AI-repo

                    # AI-repo 디렉토리로 이동
                    cd AI-repo

                    # Sparse Checkout 활성화
                    git sparse-checkout init --cone

                    # docker_jenkins 폴더만 가져오기
                    git sparse-checkout set docker_jenkins

                    # 실제 체크아웃 실행 (docker_jenkins 폴더만 가져옴)
                    git checkout ${BRANCH}

		    # 필요 없는 메타데이터 제거 (Jenkins가 전체 리포지토리를 다루지 않도록)      
		    rm -rf .git	
		    '''	    
	    }
        }
	    
        stage('Login to AWS ECR') {
            steps {
                script {
                    sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}"
                }
            }
        }

        stage('Build & Tag & Push Docker Images to ECR') {
            steps {
                script {
                    sh """
		    echo "🛑 이전 Docker 이미지 정리"
		    docker system prune -af  # 사용하지 않는 이미지, 컨테이너, 볼륨 정리
      
                    echo "🐳 Docker 이미지 빌드 시작..." 
	            cd /var/lib/jenkins/workspace/AI/AI-repo/docker_jenkins/  # ✅ 경로 이동		    
		    docker-compose -f docker-compose.build.yml build --no-cache  
      
                    echo "🏷️ Docker 이미지 태깅"                    
                    docker tag crypto_project-airflow-webserver:latest ${ECR_REPO}:webserver-${TAG}
                    docker tag crypto_project-airflow-scheduler:latest ${ECR_REPO}:scheduler-${TAG}

                    echo "📤 AWS ECR로 이미지 Push"                    
                    docker push ${ECR_REPO}:webserver-${TAG}
                    docker push ${ECR_REPO}:scheduler-${TAG}
                    
                    # 최신 버전 관리를 위해 latest 태그도 추가
                    docker tag ${ECR_REPO}:webserver-${TAG} ${ECR_REPO}:webserver-latest
                    docker tag ${ECR_REPO}:scheduler-${TAG} ${ECR_REPO}:scheduler-latest
                    docker push ${ECR_REPO}:webserver-latest
                    docker push ${ECR_REPO}:scheduler-latest
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                script {
                        sh """
                        echo "🔗 EC2(${EC2_HOST})에 배포 시작..."   
			
			echo "🗑️ 기존 프로젝트 폴더 삭제 (Airflow EC2)"
			ssh -i /var/lib/jenkins/PROFECT_OOPS\\!.pem -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "rm -rf /home/ubuntu/docker_jenkins/"
   
			echo "📁 EC2에 docker_jenkins 폴더 생성 (없으면 생성)"
			ssh -i /var/lib/jenkins/PROFECT_OOPS!\\.pem -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "mkdir -p /home/ubuntu/docker_jenkins/"
   			
      			echo "📁 최신 GitHub 코드 Airflow EC2로 복사"
			scp -i /var/lib/jenkins/PROFECT_OOPS\\!.pem -o StrictHostKeyChecking=no -r ${WORKSPACE}/AI-repo/docker_jenkins/* ${EC2_USER}@${EC2_HOST}:/home/ubuntu/docker_jenkins/

            		echo "📂 `.env` 파일을 docker_jenkins 폴더로 복사"
            		ssh -i /var/lib/jenkins/PROFECT_OOPS\\!.pem -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} "cp /home/ubuntu/.env /home/ubuntu/docker_jenkins/.env"
   
                        echo "🚀 Docker 컨테이너 업데이트"
			ssh -i /var/lib/jenkins/PROFECT_OOPS\\!.pem -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} <<EOF
AWS_REGION="ap-northeast-2"
ECR_REPO="941377153895.dkr.ecr.ap-northeast-2.amazonaws.com/oops/ai"

echo "🔑 AWS ECR 로그인"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

cd /home/ubuntu/docker_jenkins

echo "🛑 기존 컨테이너 정리 및 사용하지 않는 리소스 삭제"
docker-compose -f docker-compose.deploy.yml down || true  # 기존 컨테이너 삭제
docker system prune -af  # 사용하지 않는 이미지 & 네트워크 삭제
docker volume prune -f  # 사용하지 않는 볼륨 삭제
docker network prune -f  # 사용하지 않는 네트워크 삭제

echo "📥 최신 Docker 이미지 Pull"
docker-compose -f docker-compose.deploy.yml pull  # 🔥 최신 버전 이미지 가져오기

echo "🚀 새로운 컨테이너 실행"
docker-compose -f docker-compose.deploy.yml up -d
EOF
                        """
                 }
	    }
        }	
    }    
	
    post {
        success {
            echo "✅ 배포 완료!"
        }
        failure {
            echo "❌ 배포 실패!"
        }
    }
}
