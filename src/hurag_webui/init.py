from .dss import rss
from .kernel import logger

def main():
    rss.init_rss()
    logger().info("HuRAG 2.0 WebUI database initialized")

if __name__ == "__main__":
    main()

