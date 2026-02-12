#!/bin/bash

# World Bank IATI Intelligence Agent - Digital Ocean Deployment Script

echo "🌍 World Bank IATI Intelligence Agent - Digital Ocean Deployment"
echo "================================================================"

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Please run this script from the agent directory."
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "📋 Files to deploy:"
ls -la *.html *.css *.js *.md 2>/dev/null

echo ""
echo "🚀 Deployment Options:"
echo ""
echo "1. 📦 Create deployment archive for Digital Ocean App Platform"
echo "2. 🐳 Deploy using Docker (requires Docker CLI)"
echo "3. 📤 Upload to GitHub for GitHub Pages deployment"
echo ""

read -p "Choose deployment method (1-3): " choice

case $choice in
    1)
        echo "📦 Creating deployment archive..."

        # Create deployment directory
        mkdir -p deploy-package

        # Copy essential files
        cp index.html styles.css script.js deploy-package/
        cp README.md DEPLOYMENT_GUIDE.md deploy-package/ 2>/dev/null || true
        cp package.json Dockerfile .do/app.yaml deploy-package/ 2>/dev/null || true

        # Create archive
        cd deploy-package
        tar -czf ../wb-iati-agent-deploy.tar.gz *
        cd ..

        echo "✅ Deployment package created: wb-iati-agent-deploy.tar.gz"
        echo ""
        echo "📋 Next steps:"
        echo "1. Go to https://cloud.digitalocean.com/apps"
        echo "2. Click 'Create App'"
        echo "3. Choose 'Upload from Archive'"
        echo "4. Upload the wb-iati-agent-deploy.tar.gz file"
        echo "5. Select 'Static Site' as the service type"
        echo "6. Deploy!"
        echo ""
        echo "🌐 Your agent will be available at: https://your-app-name.ondigitalocean.app"
        ;;

    2)
        echo "🐳 Docker deployment..."

        if ! command -v docker &> /dev/null; then
            echo "❌ Docker not found. Please install Docker first."
            exit 1
        fi

        echo "Building Docker image..."
        docker build -t wb-iati-agent .

        echo "✅ Docker image built successfully!"
        echo ""
        echo "📋 To run locally:"
        echo "docker run -p 8080:8080 wb-iati-agent"
        echo ""
        echo "📋 To deploy to Digital Ocean Container Registry:"
        echo "1. docker tag wb-iati-agent registry.digitalocean.com/your-registry/wb-iati-agent"
        echo "2. docker push registry.digitalocean.com/your-registry/wb-iati-agent"
        ;;

    3)
        echo "📤 GitHub deployment preparation..."

        if [ ! -d ".git" ]; then
            echo "Initializing Git repository..."
            git init
            git add .
            git commit -m "Initial commit: World Bank IATI Intelligence Agent v1.0.0"
            echo "✅ Git repository initialized"
        else
            echo "📁 Git repository already exists"
        fi

        echo ""
        echo "📋 Next steps for GitHub Pages:"
        echo "1. Create a new repository on GitHub"
        echo "2. Add remote: git remote add origin YOUR_GITHUB_REPO_URL"
        echo "3. Push code: git push -u origin main"
        echo "4. Go to GitHub repo → Settings → Pages"
        echo "5. Enable Pages with source 'Deploy from branch' → main"
        echo "6. Your agent will be live at: https://yourusername.github.io/repo-name"
        ;;

    *)
        echo "❌ Invalid choice. Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment preparation complete!"
echo "🌍 World Bank IATI Intelligence Agent ready for the cloud! ☁️"