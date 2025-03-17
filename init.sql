USE oops;

-- ✅ 1️⃣ 테이블 존재 여부 확인 후 전체 SQL 실행
SET @table_exists = (SELECT COUNT(*) 
                     FROM information_schema.TABLES 
                     WHERE TABLE_SCHEMA = 'oops' 
                     AND (TABLE_NAME = 'news_sentiment' OR TABLE_NAME = 'coin_sentiment_stats'));

-- ✅ 2️⃣ 테이블이 없으면 실행
IF @table_exists = 0 THEN
    
    -- ✅ 1. news 테이블 변경
    ALTER TABLE news MODIFY COLUMN title VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE news MODIFY COLUMN content VARCHAR(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE news MODIFY COLUMN newspapaer VARCHAR(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
    ALTER TABLE news MODIFY COLUMN source VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
    ALTER TABLE news MODIFY COLUMN title_en VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE news MODIFY COLUMN contnet_en VARCHAR(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;

    -- ✅ 2. coin 테이블 변경
    ALTER TABLE coin MODIFY COLUMN name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL;
    ALTER TABLE coin MODIFY COLUMN prospects DECIMAL(5,2);
    ALTER TABLE coin MODIFY COLUMN coin_picture VARCHAR(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;
    ALTER TABLE coin MODIFY COLUMN ticker VARCHAR(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci UNIQUE;
    ALTER TABLE coin MODIFY COLUMN gpt_data VARCHAR(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ;

    -- ✅ 3. news_sentiment 테이블 생성 (FK 관계 설정)
    CREATE TABLE news_sentiment (
        news_id BIGINT PRIMARY KEY,
        sentiment_score DECIMAL(5,2) NOT NULL,
        sentiment_label VARCHAR(20),
        FOREIGN KEY (news_id) REFERENCES news(news_id) ON DELETE CASCADE
    );

    -- ✅ 4. coin_sentiment_stats 테이블 생성 (FK 관계 설정)
    CREATE TABLE coin_sentiment_stats (
        coin_id BIGINT NOT NULL,
        time DATETIME DEFAULT CURRENT_TIMESTAMP,
        coin_score DECIMAL(5,2) NOT NULL,
        PRIMARY KEY (coin_id, time),
        FOREIGN KEY (coin_id) REFERENCES coin(coin_id) ON DELETE CASCADE
    );
    
    -- ✅ 5. news_coin_relation 테이블 변경
    ALTER TABLE news_coin_relation ADD FOREIGN KEY (news_id) REFERENCES news(news_id) ON DELETE CASCADE;
    ALTER TABLE news_coin_relation ADD FOREIGN KEY (coin_id) REFERENCES coin(coin_id) ON DELETE CASCADE;

    -- ✅ 6. coin 테이블에 10개 코인 데이터 삽입
    INSERT INTO coin (coin_id, name, ticker, prospects, coin_picture, gpt_data) VALUES
    (1, '엑스알피', 'KRW-XRP', NULL, 'https://static.upbit.com/logos/XRP.png', 'XRP 분석 데이터'),
    (2, '비트코인', 'KRW-BTC', NULL, 'https://static.upbit.com/logos/BTC.png', 'BTC 분석 데이터'),
    (3, '이더리움', 'KRW-ETH', NULL, 'https://static.upbit.com/logos/ETH.png', 'ETH 분석 데이터'),
    (4, '퀀텀', 'KRW-QTUM', NULL, 'https://static.upbit.com/logos/QTUM.png', 'QTUM 분석 데이터'),
    (5, '웨이브', 'KRW-WAVES', NULL, 'https://static.upbit.com/logos/WAVES.png', 'WAVES 분석 데이터'),
    (6, '넴', 'KRW-XEM', NULL, 'https://static.upbit.com/logos/XEM.png', 'XEM 분석 데이터'),
    (7, '이더리움클래식', 'KRW-ETC', NULL, 'https://static.upbit.com/logos/ETC.png', 'ETC 분석 데이터'),
    (8, '네오', 'KRW-NEO', NULL, 'https://static.upbit.com/logos/NEO.png', 'NEO 분석 데이터'),
    (9, '스테이터스네트워크토큰', 'KRW-SNT', NULL, 'https://static.upbit.com/logos/SNT.png', 'SNT 분석 데이터'),
    (10, '메탈', 'KRW-MTL', NULL, 'https://static.upbit.com/logos/MTL.png', 'MTL 분석 데이터');

    UPDATE coin SET gpt_data = 
    '기본 정보: 국제 송금을 빠르고 저렴하게 처리하기 위해 개발된 코인입니다.\n
    장점: 기존 금융 시스템보다 빠른 결제 속도(3~5초)와 낮은 수수료가 강점입니다.\n
    변동성: 미국 SEC(증권거래위원회)와의 법적 분쟁이 가격에 큰 영향을 미쳐 변동성이 높습니다.\n
    초보 투자 팁: 법적 이슈 해결 여부를 주시하며 투자하는 것이 중요합니다. 변동성이 클 수 있어 분할 매수 전략을 활용하는 것이 좋습니다.'
    WHERE ticker = 'KRW-XRP';

    UPDATE coin SET gpt_data = 
    '기본 정보: 세계 최초이자 가장 유명한 암호화폐로, 디지털 금으로 불립니다.\n
    장점: 희소성이 높고(총 2100만 개 발행), 글로벌 결제 및 자산 저장 수단으로 활용됩니다.\n
    변동성: 주기적인 반감기(4년마다)와 경제 상황에 따라 가격이 급등락할 수 있습니다.\n
    초보 투자 팁: 장기 보유 전략이 효과적이며, 급격한 하락 시에도 패닉셀(공황 매도)을 피하는 것이 중요합니다.'
    WHERE ticker = 'KRW-BTC';

    UPDATE coin SET gpt_data = 
    '기본 정보: 스마트 계약 기능을 제공하는 블록체인 플랫폼으로, 다양한 DApp(탈중앙화 앱)과 NFT 생태계를 운영합니다.\n
    장점: 비트코인보다 기능이 많아 블록체인 기술의 핵심 인프라 역할을 합니다. 스테이킹(예치 후 보상)도 가능해 보유만으로 수익을 낼 수 있습니다.\n
    변동성: 업그레이드 및 네트워크 사용량에 따라 가격 변동성이 큽니다.\n
    초보 투자 팁: 장기적으로 성장 가능성이 크므로, 꾸준한 관찰과 분할 매수가 유리합니다.'
    WHERE ticker = 'KRW-ETH';

    UPDATE coin SET gpt_data = 
    '기본 정보: 비트코인과 이더리움의 장점을 결합한 하이브리드 블록체인으로, 스마트 계약 기능을 제공합니다.\n
    장점: 기업과 개발자가 쉽게 사용할 수 있도록 설계되었으며, 확장성이 높습니다.\n
    변동성: 거래량이 적어 가격 변동성이 상대적으로 큽니다.\n
    초보 투자 팁: 단기 투기보다는 장기적 기술 발전을 확인하며 투자하는 것이 좋습니다.'
    WHERE ticker = 'KRW-QTUM';

    UPDATE coin SET gpt_data = 
    '기본 정보: 빠르고 저렴한 거래를 위해 개발된 블록체인 플랫폼으로, 맞춤형 토큰 발행이 가능합니다.\n
    장점: 개인이나 기업이 쉽게 자체 암호화폐를 만들 수 있어 활용성이 높습니다.\n
    변동성: 거래소 내 활용도와 개발 방향에 따라 가격이 급변할 수 있습니다.\n
    초보 투자 팁: 프로젝트 개발 동향을 주시하며, 유망한 파트너십이 있는지 확인하는 것이 중요합니다.'
    WHERE ticker = 'KRW-WAVES';

    UPDATE coin SET gpt_data = 
    '기본 정보: 기업과 금융 기관을 위한 블록체인 솔루션으로 설계된 코인입니다.\n
    장점: 빠른 트랜잭션 속도와 낮은 수수료가 특징이며, 보안성이 높습니다.\n
    변동성: 사용 사례 증가에 따라 가격이 영향을 받을 수 있습니다.\n
    초보 투자 팁: 실제 기업 도입 사례를 분석하고, 장기적 관점에서 접근하는 것이 유리합니다.'
    WHERE ticker = 'KRW-XEM';

    UPDATE coin SET gpt_data = 
    '기본 정보: 이더리움에서 분리된 블록체인으로, 원래의 이더리움 철학을 고수하는 프로젝트입니다.\n
    장점: 탈중앙화 철학을 지키며, 보안성이 높아 일부 투자자에게 매력적입니다.\n
    변동성: 개발 및 채택 속도가 느려 상대적으로 성장성이 제한적일 수 있습니다.\n
    초보 투자 팁: 장기 보유보다는 기술적 변화 및 시장 흐름을 주시하며 단기 투자하는 것이 유리합니다.'
    WHERE ticker = 'KRW-ETC';

    UPDATE coin SET gpt_data = 
    '기본 정보: 중국에서 개발된 스마트 계약 블록체인으로, 이더리움과 유사하지만 개발 친화적인 환경을 제공합니다.\n
    장점: 중국 정부와의 연계 가능성이 있어, 아시아 시장에서 영향력이 큽니다.\n
    변동성: 중국 정부 규제에 영향을 받을 수 있으며, 가격 변동성이 높습니다.\n
    초보 투자 팁: 중국 규제 및 시장 환경을 지속적으로 체크하는 것이 중요합니다.'
    WHERE ticker = 'KRW-NEO';

    UPDATE coin SET gpt_data = 
    '기본 정보: 이더리움 기반의 메신저 및 웹3.0 플랫폼으로, 분산형 앱(DApp)과의 연결을 돕습니다.\n
    장점: 개인 정보 보호와 탈중앙화 커뮤니케이션 기능이 강점입니다.\n
    변동성: 시장의 관심 여부에 따라 유동성이 낮아질 수 있습니다.\n
    초보 투자 팁: 해당 프로젝트의 성장성과 실제 사용자 증가 여부를 확인하는 것이 중요합니다.'
    WHERE ticker = 'KRW-SNT';

    UPDATE coin SET gpt_data = 
    '기본 정보: 모바일 결제를 위한 블록체인 프로젝트로, 암호화폐 보상 시스템을 갖추고 있습니다.\n
    장점: 사용자가 코인을 쉽게 얻고 사용할 수 있도록 설계되어 접근성이 좋습니다.\n
    변동성: 결제 시스템 확장 여부에 따라 가치가 달라질 수 있습니다.\n
    초보 투자 팁: 실제 사용처와 결제 파트너십 확대 여부를 분석하며 투자하는 것이 중요합니다.'
    WHERE ticker = 'KRW-MTL';

END IF;
