PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO alembic_version VALUES('ca7037a8accb');
CREATE TABLE followers (
	follower_id INTEGER, 
	followed_id INTEGER, timestamp DATETIME, 
	CONSTRAINT fk_followers_followed_id_users FOREIGN KEY(followed_id) REFERENCES users (id), 
	CONSTRAINT fk_followers_follower_id_users FOREIGN KEY(follower_id) REFERENCES users (id)
);
INSERT INTO followers VALUES(1,2,'2020-05-11 06:05:06.174951');
INSERT INTO followers VALUES(6,1,'2020-05-13 09:03:53.419661');
INSERT INTO followers VALUES(1,6,'2020-05-13 12:52:28.106438');
INSERT INTO followers VALUES(8,1,'2020-05-13 15:23:15.307420');
INSERT INTO followers VALUES(8,6,'2020-05-13 15:23:31.133315');
CREATE TABLE comments_likes (
	user_id INTEGER, 
	comment_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_comments_likes_comment_id_comments FOREIGN KEY(comment_id) REFERENCES comments (id), 
	CONSTRAINT fk_comments_likes_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO comments_likes VALUES(2,2,'2020-05-12 10:50:09.806474');
CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	name VARCHAR(128), 
	user_id INTEGER, 
	timestamp FLOAT, 
	payload_json TEXT, 
	CONSTRAINT pk_notifications PRIMARY KEY (id), 
	CONSTRAINT fk_notifications_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO notifications VALUES(2,'unread_messages_count',2,1589207409.4387478828,'1');
INSERT INTO notifications VALUES(3,'unread_messages_count',3,1589209250.0936164855,'3');
INSERT INTO notifications VALUES(8,'unread_comments_likes_count',2,1589280613.359187603,'0');
INSERT INTO notifications VALUES(9,'unread_comments_likes_count',1,1589301406.7336258888,'0');
INSERT INTO notifications VALUES(17,'unread_microcons_likes_count',1,1589340755.6696896552,'0');
INSERT INTO notifications VALUES(31,'unread_followeds_micropubs_count',10,1589371689.5964732169,'0');
INSERT INTO notifications VALUES(32,'unread_followeds_microcons_count',10,1589371690.203263998,'0');
INSERT INTO notifications VALUES(45,'unread_followeds_microcons_count',1,1589372868.2230448722,'0');
INSERT INTO notifications VALUES(68,'unread_followeds_micropubs_count',1,1589374295.3126375675,'0');
INSERT INTO notifications VALUES(97,'unread_micropubs_likes_count',8,1589381813.4105978011,'0');
INSERT INTO notifications VALUES(98,'unread_recived_comments_count',8,1589381813.9289062023,'0');
INSERT INTO notifications VALUES(115,'unread_followeds_microcons_count',6,1589382190.3767242431,'0');
INSERT INTO notifications VALUES(116,'unread_followeds_micropubs_count',6,1589382454.4553823471,'0');
INSERT INTO notifications VALUES(118,'unread_microcons_likes_count',6,1589382456.4800417423,'0');
INSERT INTO notifications VALUES(119,'unread_micropubs_likes_count',6,1589382458.3135030269,'0');
INSERT INTO notifications VALUES(120,'unread_recived_comments_count',6,1589382458.8234288692,'0');
INSERT INTO notifications VALUES(122,'unread_micropubs_likes_count',1,1589383174.2467164993,'2');
INSERT INTO notifications VALUES(123,'unread_recived_comments_count',1,1589383188.987613201,'1');
INSERT INTO notifications VALUES(124,'unread_messages_count',1,1589383375.5160973071,'2');
INSERT INTO notifications VALUES(129,'unread_followeds_micropubs_count',8,1589383642.0240550041,'0');
INSERT INTO notifications VALUES(130,'unread_followeds_microcons_count',8,1589383642.5030617714,'0');
INSERT INTO notifications VALUES(131,'unread_follows_count',8,1589383664.7325527667,'0');
INSERT INTO notifications VALUES(138,'unread_follows_count',6,1589384122.3501265049,'0');
INSERT INTO notifications VALUES(143,'unread_follows_count',1,1589384148.4199926853,'0');
INSERT INTO notifications VALUES(144,'unread_messages_count',6,1589384168.4794139862,'0');
INSERT INTO notifications VALUES(145,'unread_follows_count',2,1589384176.3457274437,'0');
CREATE TABLE messages (
	id INTEGER NOT NULL, 
	body TEXT, 
	timestamp DATETIME, 
	sender_id INTEGER, 
	recipient_id INTEGER, 
	CONSTRAINT pk_messages PRIMARY KEY (id), 
	CONSTRAINT fk_messages_recipient_id_users FOREIGN KEY(recipient_id) REFERENCES users (id), 
	CONSTRAINT fk_messages_sender_id_users FOREIGN KEY(sender_id) REFERENCES users (id)
);
INSERT INTO messages VALUES(1,'this is a message','2020-05-11 14:30:09.429767',1,2);
INSERT INTO messages VALUES(2,'this is a message','2020-05-11 14:30:19.675738',1,3);
INSERT INTO messages VALUES(3,'this is a message','2020-05-11 15:00:20.642363',1,3);
INSERT INTO messages VALUES(4,'this is another message','2020-05-11 15:00:50.086635',1,3);
INSERT INTO messages VALUES(5,'test','2020-05-13 09:04:02.619522',6,1);
INSERT INTO messages VALUES(6,replace('test\n','\n',char(10)),'2020-05-13 09:04:51.672564',6,1);
INSERT INTO messages VALUES(7,'test','2020-05-13 12:51:55.373767',1,6);
INSERT INTO messages VALUES(8,'Это предположение было принято.','2020-05-13 13:01:18.903176',6,1);
INSERT INTO messages VALUES(9,'hello~~~','2020-05-13 15:22:55.505022',8,1);
CREATE TABLE blacklist (
	user_id INTEGER, 
	block_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_blacklist_block_id_users FOREIGN KEY(block_id) REFERENCES users (id), 
	CONSTRAINT fk_blacklist_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE micropubs_likes (
	user_id INTEGER, 
	micropub_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_micropubs_likes_micropub_id_micropubs FOREIGN KEY(micropub_id) REFERENCES micropubs (id), 
	CONSTRAINT fk_micropubs_likes_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE roles (
	id INTEGER NOT NULL, 
	slug VARCHAR(255), 
	name VARCHAR(255), 
	"default" BOOLEAN, 
	permissions INTEGER, 
	CONSTRAINT pk_roles PRIMARY KEY (id), 
	CONSTRAINT uq_roles_slug UNIQUE (slug), 
	CONSTRAINT ck_roles_default CHECK ("default" IN (0, 1))
);
INSERT INTO roles VALUES(1,'shutup','小黑屋',0,0);
INSERT INTO roles VALUES(2,'reader','读者',1,3);
INSERT INTO roles VALUES(3,'author','作者',0,7);
INSERT INTO roles VALUES(4,'administrator','管理员',0,135);
CREATE TABLE IF NOT EXISTS "users" (
	id INTEGER NOT NULL, 
	username VARCHAR(64), 
	email VARCHAR(120), 
	password_hash VARCHAR(128), 
	name VARCHAR(64), 
	location VARCHAR(64), 
	about_me TEXT, 
	member_since DATETIME, 
	last_seen DATETIME, 
	last_recived_comments_read_time DATETIME, 
	last_followeds_micropubs_read_time DATETIME, 
	last_follows_read_time DATETIME, 
	last_messages_read_time DATETIME, 
	last_comments_likes_read_time DATETIME, 
	last_micropubs_likes_read_time DATETIME, 
	confirmed BOOLEAN, 
	role_id INTEGER, last_followeds_microcons_read_time DATETIME, last_microcons_likes_read_time DATETIME, 
	CONSTRAINT pk_users PRIMARY KEY (id), 
	CHECK (confirmed IN (0, 1)), 
	CONSTRAINT fk_users_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id)
);
INSERT INTO users VALUES(1,'charj99','charj99@buaa.edu.cn','pbkdf2:sha256:50000$kDIOqwPs$704a47b2ea3e9a03198889f082c7871340575cf009208cb37462fb353882be14',NULL,NULL,NULL,'2020-05-11 04:39:20.895134','2020-05-13 14:20:28.934450','2020-05-13 12:43:07.478865','2020-05-13 12:51:35.297436','2020-05-13 15:35:48.410784','2020-05-13 09:04:51.672564','2020-05-12 10:50:38.004004','2020-05-13 03:34:23.744439',1,4,'2020-05-13 12:27:48.208812','2020-05-13 03:32:35.645794');
INSERT INTO users VALUES(2,'2','777777777@qq.com','pbkdf2:sha256:50000$Q2FjS3jE$4c833277d733791e5ffc82a0b7cce39330ae09c86c8fad4155f0b021a5695974',NULL,NULL,NULL,'2020-05-11 04:45:32.172725','2020-05-13 03:01:36.514911',NULL,NULL,'2020-05-13 15:36:16.331043',NULL,NULL,NULL,1,2,NULL,NULL);
INSERT INTO users VALUES(3,'3','3@buaa.edu.cn','pbkdf2:sha256:50000$fBbgKecY$a75a2edcdc8766b212e6d810f26d10e9a4053d6a6ec95d845e6313f090114b88',NULL,NULL,NULL,'2020-05-11 04:51:48.333590','2020-05-12 16:23:28.158477',NULL,NULL,NULL,NULL,NULL,NULL,1,2,NULL,NULL);
INSERT INTO users VALUES(4,'4','4@buaa.edu.cn','pbkdf2:sha256:50000$mG9ZyLEz$a720246e663af27747d366f35a2a8b7671ff7edcefd069d784bdee00fe37308c',NULL,NULL,NULL,'2020-05-11 05:25:03.316322','2020-05-12 16:24:27.784664',NULL,NULL,NULL,NULL,NULL,NULL,1,2,NULL,NULL);
INSERT INTO users VALUES(5,'5','5@buaa.edu.cn','pbkdf2:sha256:50000$BDi4k4gP$ae1afeab847a02446c0efc51d4b70290edebf2ae7eb8995084a91a24ab02d100',NULL,NULL,NULL,'2020-05-11 05:25:10.767157','2020-05-12 16:25:15.652806',NULL,NULL,NULL,NULL,NULL,NULL,1,2,NULL,NULL);
INSERT INTO users VALUES(6,'test','2962928213@qq.com','pbkdf2:sha256:50000$Qr8M6Rfy$c52653491cabd45f97f15bf3208d536c37c68cfd566a9ad1ec909bc5e3dd7d0d',NULL,NULL,NULL,'2020-05-13 09:01:09.480465','2020-05-13 15:36:36.376399','2020-05-13 15:07:38.814197','2020-05-13 15:07:34.427773','2020-05-13 15:35:22.342135','2020-05-13 12:51:55.373767',NULL,'2020-05-13 15:07:38.299452',1,4,'2020-05-13 15:03:10.368294','2020-05-13 15:07:36.468704');
INSERT INTO users VALUES(8,'Ryan0v0','sxxhgz@163.com','pbkdf2:sha256:50000$zan798LU$c0b9afb884b15a6828ed2edd27c6da7b3de73ed8ac80faf17cb3642f2fbb5884',NULL,NULL,NULL,'2020-05-13 10:48:21.219799','2020-05-13 15:36:39.238888','2020-05-13 14:56:53.920131','2020-05-13 15:27:22.011570','2020-05-13 15:27:44.708806',NULL,NULL,'2020-05-13 14:56:53.401671',1,2,'2020-05-13 15:27:22.494376',NULL);
INSERT INTO users VALUES(9,'weekends','736756194@qq.com','pbkdf2:sha256:50000$wJzOLkMf$107fbd6837ad32ee6bd85dde5980fd3770bfb9450d9b818bcbaeac57daf34d5c',NULL,NULL,NULL,'2020-05-13 11:19:44.898762','2020-05-13 11:19:44.898776',NULL,NULL,NULL,NULL,NULL,NULL,0,2,NULL,NULL);
CREATE TABLE tasks (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(128), 
	description VARCHAR(128), 
	user_id INTEGER, 
	complete BOOLEAN, 
	CONSTRAINT pk_tasks PRIMARY KEY (id), 
	CONSTRAINT fk_tasks_user_id_users FOREIGN KEY(user_id) REFERENCES users (id), 
	CONSTRAINT ck_tasks_complete CHECK (complete IN (0, 1))
);
CREATE TABLE microcons (
	id INTEGER NOT NULL, 
	title VARCHAR(255), 
	summary VARCHAR(255), 
	author_id INTEGER, 
	timestamp DATETIME, 
	views INTEGER, status INTEGER, 
	CONSTRAINT pk_microcons PRIMARY KEY (id), 
	CONSTRAINT fk_microcons_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
);
INSERT INTO microcons VALUES(1,'microcon_1','Create microcon 1.',1,'2020-05-11 05:46:36.012490',10,1);
INSERT INTO microcons VALUES(2,'microcon_2','Create microcon 2.',1,'2020-05-11 05:47:29.365689',3,0);
INSERT INTO microcons VALUES(3,'microcon_3','Create microcon 3.',2,'2020-05-11 05:50:26.427072',5,0);
INSERT INTO microcons VALUES(4,'测试','测试内容',6,'2020-05-13 12:37:15.513407',2,0);
INSERT INTO microcons VALUES(5,'Test','Test',6,'2020-05-13 12:50:30.316089',8,0);
CREATE TABLE microcons_collects (
	user_id INTEGER, 
	microcon_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_microcons_collects_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_microcons_collects_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE microcons_cons (
	microcon_id INTEGER, 
	user_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_microcons_cons_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_microcons_cons_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO microcons_cons VALUES(2,2,'2020-05-11 06:30:47.417735');
INSERT INTO microcons_cons VALUES(5,1,'2020-05-13 12:52:36.040954');
INSERT INTO microcons_cons VALUES(3,6,'2020-05-13 12:53:57.361573');
CREATE TABLE microcons_likes (
	user_id INTEGER, 
	microcon_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_microcons_likes_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_microcons_likes_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO microcons_likes VALUES(2,1,'2020-05-13 03:01:36.656433');
CREATE TABLE microcons_micropubs (
	micropub_id INTEGER, 
	microcon_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_microcons_micropubs_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_microcons_micropubs_micropub_id_micropubs FOREIGN KEY(micropub_id) REFERENCES micropubs (id)
);
INSERT INTO microcons_micropubs VALUES(1,1,'2020-05-11 05:46:36.297277');
INSERT INTO microcons_micropubs VALUES(1,2,'2020-05-11 05:47:29.692185');
INSERT INTO microcons_micropubs VALUES(4,3,'2020-05-11 05:50:26.597740');
INSERT INTO microcons_micropubs VALUES(74,4,'2020-05-13 12:37:15.532341');
INSERT INTO microcons_micropubs VALUES(17,4,'2020-05-13 12:37:15.556088');
INSERT INTO microcons_micropubs VALUES(72,5,'2020-05-13 12:50:30.339548');
INSERT INTO microcons_micropubs VALUES(71,5,'2020-05-13 12:50:30.358323');
CREATE TABLE microcons_pors (
	microcon_id INTEGER, 
	user_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_microcons_pors_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_microcons_pors_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO microcons_pors VALUES(1,2,'2020-05-11 06:16:38.830020');
INSERT INTO microcons_pors VALUES(3,1,'2020-05-12 15:50:10.904197');
INSERT INTO microcons_pors VALUES(1,3,'2020-05-12 16:23:28.326029');
INSERT INTO microcons_pors VALUES(1,4,'2020-05-12 16:24:28.059928');
CREATE TABLE micropubs_collects (
	user_id INTEGER, 
	micropub_id INTEGER, 
	timestamp DATETIME, 
	CONSTRAINT fk_micropubs_collects_micropub_id_micropubs FOREIGN KEY(micropub_id) REFERENCES micropubs (id), 
	CONSTRAINT fk_micropubs_collects_user_id_users FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO micropubs_collects VALUES(6,72,'2020-05-13 12:18:44.635252');
INSERT INTO micropubs_collects VALUES(6,17,'2020-05-13 12:36:36.276056');
INSERT INTO micropubs_collects VALUES(6,71,'2020-05-13 12:36:39.178909');
INSERT INTO micropubs_collects VALUES(6,74,'2020-05-13 12:36:46.578846');
INSERT INTO micropubs_collects VALUES(6,2,'2020-05-13 12:37:20.772389');
INSERT INTO micropubs_collects VALUES(6,4,'2020-05-13 12:37:24.600709');
INSERT INTO micropubs_collects VALUES(6,6,'2020-05-13 12:37:28.423549');
INSERT INTO micropubs_collects VALUES(6,5,'2020-05-13 12:37:32.646775');
INSERT INTO micropubs_collects VALUES(6,13,'2020-05-13 12:37:45.856605');
INSERT INTO micropubs_collects VALUES(6,16,'2020-05-13 12:37:52.039755');
INSERT INTO micropubs_collects VALUES(6,26,'2020-05-13 12:37:59.781415');
INSERT INTO micropubs_collects VALUES(6,14,'2020-05-13 12:38:05.709321');
INSERT INTO micropubs_collects VALUES(6,12,'2020-05-13 12:38:22.530187');
INSERT INTO micropubs_collects VALUES(6,8,'2020-05-13 12:38:28.533829');
INSERT INTO micropubs_collects VALUES(8,51,'2020-05-13 15:19:38.080562');
CREATE TABLE tags (
	id INTEGER NOT NULL, 
	content VARCHAR(64), 
	micropub_id INTEGER, 
	microcon_id INTEGER, 
	CONSTRAINT pk_tags PRIMARY KEY (id), 
	CONSTRAINT fk_tags_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id), 
	CONSTRAINT fk_tags_micropub_id_micropubs FOREIGN KEY(micropub_id) REFERENCES micropubs (id)
);
INSERT INTO tags VALUES(32,'基于OBE理念的"软件工程"课程重塑','研究和分析了当前广泛开展的OBE教育方法,结合清华大学软件工程专业的软件工程教学,基于OBE理念对整个教学方案进行了改造和优化,重新设计了课程学习目标、教学内容框架、项目实践方法和课程实验环境等部分.重塑后的教学方案体现"价值塑造、能力培养、知识传授"的教学思想,以学生的课程学习效果为目标驱动,注重软件技术能力、工程实践能力以及解决复杂软件问题能力的培养,实施先进的工程教育教学方法,通过科学的评价','2020-05-13 15:57:39.402059');
INSERT INTO tags VALUES(33,'基于多目标优化算法NSGA-Ⅱ推荐相似缺陷报告','在软件开发过程中,开发人员会收到用户提交的大量缺陷报告.若修复缺陷报告中问题涉及到的相同源代码文件数目超过一半,则称这些缺陷报告为相似缺陷报告.给开发人员推荐相似缺陷报告能够有效节约开发人员修复缺陷的时间.该文提出一种基于多目标优化算法NSGA-Ⅱ推荐相似缺陷报告的方法,即在推荐尽可能少的相似缺陷报告情况下,使得缺陷报告间的相似度尽可能大.为此,利用缺陷报告的摘要和描述信息,该文采用TF-IDF和','2020-05-13 15:57:39.582848');
INSERT INTO tags VALUES(34,'基于卷积神经网络的代价敏感软件缺陷预测模型','基于机器学习的软件缺陷预测方法受到软件工程领域学者们的普遍关注,通过缺陷预测模型可一定程度地分析软件中的缺陷分布,以此帮助软件质量保障团队发现软件中潜在的错误并合理分配测试资源.然而,现有多数的缺陷预测方法是基于代码行数、模块依赖程度、栈引用深度等人工提取的软件特征进行缺陷预测的.此类方法未考虑到软件源码中潜在的语义特征,可能导致预测效果不理想.为了解决以上问题,文中利用卷积神经网络挖掘源码中隐含','2020-05-13 15:57:39.741515');
INSERT INTO tags VALUES(35,'军用软件测评实验室测评管理度量模型设计与实现?','为解决军用软件测评实验室对测评项目管理的不足,在现行软件工程相关的国际、国/军标指导下,基于软件研制能力成熟度模型技术和实用软件度量技术,设计并实现了一种军用软件测评实验室测评管理度量模型.模型建立针对质量和进度的度量体系和评价方法,以客观、量化和高效的方式实现对测试项目的定量评估,达到量化管理的目标,提升军用软件测评实验室对测评项目的管理能力.','2020-05-13 15:57:39.891113');
INSERT INTO tags VALUES(36,'生产建设项目水土保持“天地一体化”监管模式研究','为加强地区水土保持监测信息化工作,根据全国水土保持信息化工作要求和实际业务工作需要,结合相关技术规定要求,提出了一套生产建设项目水土保持“天地一体化”监管信息采集与管理解决方案,并在此基础上运用软件工程的方法设计了对应的生产建设项目水土保持“天地一体化”监管系统和配套的“外业辅助移动端”软件.生产建设项目水土保持“天地一体化”监管系统主要是利用遥感影像对新增地表动土开展遥感动态监测,快速、准确地获','2020-05-13 15:57:40.297108');
INSERT INTO tags VALUES(172,'三角分解',40,NULL);
INSERT INTO tags VALUES(173,'水印鲁棒性',40,NULL);
INSERT INTO tags VALUES(174,'服务拆分',41,NULL);
INSERT INTO tags VALUES(175,'图转换',41,NULL);
INSERT INTO tags VALUES(176,'非集中式服务组合方法',41,NULL);
INSERT INTO tags VALUES(177,'服务组合',41,NULL);
INSERT INTO tags VALUES(178,'过程划分',41,NULL);
INSERT INTO tags VALUES(179,'轨迹数据',42,NULL);
INSERT INTO tags VALUES(180,'隐私保护',42,NULL);
INSERT INTO tags VALUES(181,'兴趣区域',42,NULL);
INSERT INTO tags VALUES(182,'差分隐私',42,NULL);
INSERT INTO tags VALUES(183,'软件工程',43,NULL);
INSERT INTO tags VALUES(184,'实践训练',43,NULL);
INSERT INTO tags VALUES(185,'实验教学',43,NULL);
INSERT INTO tags VALUES(186,'校企合作',43,NULL);
INSERT INTO tags VALUES(187,'深度记忆网络',44,NULL);
INSERT INTO tags VALUES(188,'self-attention机制',44,NULL);
INSERT INTO tags VALUES(189,'细粒度情感分析',44,NULL);
INSERT INTO tags VALUES(190,'依存句法分析',44,NULL);
INSERT INTO tags VALUES(191,'情感需求',44,NULL);
INSERT INTO tags VALUES(192,'文本情感分类',45,NULL);
INSERT INTO tags VALUES(193,'textSE-ResNeXt',45,NULL);
INSERT INTO tags VALUES(194,'特征划分',45,NULL);
INSERT INTO tags VALUES(195,'集成模型',45,NULL);
INSERT INTO tags VALUES(196,'知识图谱',46,NULL);
INSERT INTO tags VALUES(197,'协同过滤',46,NULL);
INSERT INTO tags VALUES(198,'推荐系统',46,NULL);
INSERT INTO tags VALUES(199,'可解释性推荐',46,NULL);
INSERT INTO tags VALUES(200,'文本分类',47,NULL);
INSERT INTO tags VALUES(201,'CHI方法',47,NULL);
INSERT INTO tags VALUES(202,'特征提取',47,NULL);
INSERT INTO tags VALUES(203,'K-means算法',47,NULL);
INSERT INTO tags VALUES(204,'自适应算法',47,NULL);
INSERT INTO tags VALUES(205,'课程特点',48,NULL);
INSERT INTO tags VALUES(206,'实践创新',48,NULL);
INSERT INTO tags VALUES(207,'科研创新',48,NULL);
INSERT INTO tags VALUES(208,'变异测试',49,NULL);
INSERT INTO tags VALUES(209,'变异算子',49,NULL);
INSERT INTO tags VALUES(210,'等价变异体',49,NULL);
INSERT INTO tags VALUES(211,'错误定位',49,NULL);
INSERT INTO tags VALUES(212,'程序理解',50,NULL);
INSERT INTO tags VALUES(213,'程序分析',50,NULL);
INSERT INTO tags VALUES(214,'软件工程',50,NULL);
INSERT INTO tags VALUES(215,'深度学习',50,NULL);
INSERT INTO tags VALUES(216,'数据挖掘',50,NULL);
INSERT INTO tags VALUES(217,'健身',51,NULL);
CREATE TABLE IF NOT EXISTS "comments" (
	id INTEGER NOT NULL, 
	body TEXT, 
	timestamp DATETIME, 
	disabled BOOLEAN, 
	author_id INTEGER, 
	micropub_id INTEGER, 
	mark_read BOOLEAN, 
	parent_id INTEGER, 
	microcon_id INTEGER, 
	CONSTRAINT pk_comments PRIMARY KEY (id), 
	CHECK (disabled IN (0, 1)), 
	CHECK (mark_read IN (0, 1)), 
	CONSTRAINT fk_comments_micropub_id_micropubs FOREIGN KEY(micropub_id) REFERENCES micropubs (id), 
	CONSTRAINT fk_comments_author_id_users FOREIGN KEY(author_id) REFERENCES users (id), 
	CONSTRAINT fk_comments_parent_id_comments FOREIGN KEY(parent_id) REFERENCES comments (id) ON DELETE CASCADE, 
	CONSTRAINT fk_comments_microcon_id_microcons FOREIGN KEY(microcon_id) REFERENCES microcons (id)
);
INSERT INTO comments VALUES(2,'this is a good microcon','2020-05-12 09:17:23.378907',0,1,NULL,0,NULL,1);
INSERT INTO comments VALUES(3,'this is a good micropub','2020-05-12 09:47:49.930324',0,1,1,0,NULL,NULL);
INSERT INTO comments VALUES(4,'You are correct','2020-05-12 09:47:59.174019',0,1,1,0,1,NULL);
INSERT INTO comments VALUES(5,'这是一个很好的微证据','2020-05-13 12:21:06.261400',0,6,72,0,NULL,NULL);
INSERT INTO comments VALUES(6,'Русский текст: это хорошее доказательство','2020-05-13 12:21:49.159234',0,6,72,0,NULL,NULL);
INSERT INTO comments VALUES(7,'Это предположение было принято.','2020-05-13 13:01:01.783395',0,6,NULL,0,NULL,1);
INSERT INTO comments VALUES(8,'发展体育运动，增强人民体质','2020-05-13 15:19:48.951319',0,8,51,0,NULL,NULL);
CREATE TABLE IF NOT EXISTS "micropubs" (
	id INTEGER NOT NULL, 
	title VARCHAR(255), 
	summary TEXT, 
	timestamp DATETIME, 
	views INTEGER, 
	author_id INTEGER, 
	reference VARCHAR(255), 
	CONSTRAINT pk_micropubs PRIMARY KEY (id), 
	CONSTRAINT fk_micropubs_author_id_users FOREIGN KEY(author_id) REFERENCES users (id)
);
INSERT INTO micropubs VALUES(1,'智能软件工程专栏前言',replace(replace('软件作为信息社会的基础设施,深刻地影响着现代人类文明的进程.自 1968 年软件工程的概念被提出以来,如何高效地开发高质量的软件一直是计算机科学的研究热点.近年来,随着人工智能技术的发展,人工智能与软件工程开始深度融合,由此形成的全新学科交叉方向——智能软件工程成为了国内外学者关注的焦点和研究重点.\r\n智能软件工程主要涵盖两方面:人工智能赋能的软件工程和面向人工智能的软件工程.一方面,以深度学习为','\r',char(13)),'\n',char(10)),'2020-05-13 15:57:30.404888',0,1,'江贺, 郝丹, 许畅, 彭鑫');
INSERT INTO micropubs VALUES(2,'面向工程教育认证的"GIS软件工程"实践教学研究','以中国地质大学地理信息系统专业《GIS软件工程》实践教学为例,探讨了在"新工科"和"工程教育认证"背景下"GIS 软件工程"实践课程的教学过程设计.以培养学生解决复杂工程问题为目标,分析了华盛顿协议12条毕业要求与教学设计内容之间的映射关系,以期为相关新工科培养目标下的教学改革提供参考.','2020-05-13 15:57:30.779256',0,1,'杨林, 李圣文, 左泽均, 叶亚琴');
INSERT INTO micropubs VALUES(3,'FMECA在雷达软件工程中的应用','在雷达软件开发时,需要把可靠性分析技术应用到软件开发中,识别软件故障模式,形成软件故障预防措施.文中主要研究如何在雷达软件需求开发和设计中使用可靠性分析技术,并以雷达系统中典型软件为例提出在软件工程过程中实施功能故障模式、影响及危害性分析(FMECA)和软件FMECA的技术途径.','2020-05-13 15:57:30.924878',0,1,'杨润亭, 徐频频, 仇芝');
INSERT INTO micropubs VALUES(4,'新工科背景下基于价值引导的软件工程专业教学建设','新工科背景下,开展多元化、创新型的卓越人才培养离不开价值引导,在高等教育"双一流"建设的契机下,坚持立德树人,对传统工科进行改造是工科类专业建设一流本科教育的目标追求.本文围绕价值引导,针对新工科改革内容,在育人文化、培养体系和教学管理过程等方面进行初步探索与实践,通过构建价值引导下的文化理念、教育价值生态、人才培育体系,将价值引导贯穿于教学育人培养全流程,取得了一定的效果与经验.','2020-05-13 15:57:31.068905',0,1,'陈志刚, 夏旭, 廖志芳, 刘莉平, 刘佳琦');
INSERT INTO micropubs VALUES(5,'面向军事信息系统的自动化软件部署算法','当前大型军事信息系统部署是一个关键问题,现有的自动部署软件如Jenkins、apt、Docker等软件无法满足大型信息系统软件种类繁多、软件依赖关系复杂、跨平台部署等需求,因此本文首先提出一套规范化的软件部署模型,并且通过文档架构描述(以下简称XSD)进行描述,其次在依赖冲突检测算法的基础上,通过改进深度优先遍历算法(DSP),提出软件部署序列生成算法,并对该算法进行实验验证.','2020-05-13 15:57:31.224684',0,1,'戴文博, 徐珞, 卫津逸');
INSERT INTO micropubs VALUES(6,'面向软件生态的资源定位技术','为满足大型复杂软件系统定制需求,软件生态系统应运而生,并逐渐成为软件工程领域新的发展趋势,如何准确快速地定位软件资源成为关键问题.本文以本体为基础给出软件生态系统模型,保证不同软件资源能够进行统一描述,在此基础上,提出一种基于统一访问引擎的软件资源快速访问技术,从而保证能够精确获取不同软件资源库的软件资源,满足软件生态系统中不同组织、大量软件的精细化管理需求.实验表明,本文提出的资源管理技术能够大','2020-05-13 15:57:31.391369',0,1,'李华莹, 刘丽, 刘怡静');
INSERT INTO micropubs VALUES(7,'跨项目软件缺陷预测方法研究综述','软件缺陷预测是提高软件测试效率、保证软件可靠性的重要途径,已经成为目前实证软件工程领域的研究热点.在软件工程中,软件的开发过程或技术平台可能随时变化,特别是遇到新项目启动或旧项目重新开发时,基于目标项目数据的传统软件缺陷预测方法无法满足实践需求.基于迁移学习技术采用其他项目中已经标注的软件数据实现跨项目的缺陷预测,可以有效解决传统方法的不足,引起了国内外研究者的极大关注,并取得了一系列的研究成果.','2020-05-13 15:57:31.835078',0,1,'李勇, 刘战东, 张海军');
INSERT INTO micropubs VALUES(8,'突发公共卫生事件监测与防控体系的软件设计','突发公共卫生事件是指在某些国家或地区突然发生的,使民众生命、生活、生产受到严重威胁的大规模传染性流行疾病事件.在现代社会中,个体接受的信息多、随机移动半径大且移动速度快、进入密集人群的可能性大,当发生突发公共卫生事件时,采用传统流行病学调查等手段,不能准确地监测到个体行为轨迹和接触史,很难建立起有效阻止疾病蔓延的防控体系.观察了我国近期发生的新冠肺炎大规模流行事件和抗击疫情中的信息化应用状况;特别','2020-05-13 15:57:32.178760',0,1,'罗铁坚, 孙一涵, 罗晨希');
INSERT INTO micropubs VALUES(9,'电力业务中台技术标准体系研究','针对电力企业中台建设缺乏技术标准体系支撑的问题,基于企业架构方法、领域驱动设计方法、软件工程相关标准,结合国家电网有限公司"网上国网"项目业务中台建设实践经验,形成电力业务中台技术标准体系,从通用设计、业务设计、架构设计、系统设计、服务研发、运营治理6个方面,系统性地提出了电力业务中台技术标准体系的构建原则及方法,形成了电力业务中台技术标准体系,为电力业务中台的建设提供具体的设计指导和操作方法,为','2020-05-13 15:57:32.527598',0,1,'戴永新, 张紫淇, 欧阳红, 朱平飞, 袁葆, 刘玉玺');
INSERT INTO micropubs VALUES(10,'VR手术视频示教平台的构建与应用','目的:针对传统数字手术视频示教平台视角受限、交互性差、移动观看不便等问题,构建VR手术视频示教平台.方法:采用客户端/服务器(Client/Server,C/S)架构,在Visual Studio平台上基于HTML 5技术,利用软件工程的思想设计并实现包括采集制作模块和终端播放模块的VR手术视频示教平台.结果:该平台可提供佩戴VR眼镜及裸眼2种观看模式,便于在移动端随时随地学习,可实现VR全景手术','2020-05-13 15:57:32.926435',0,1,'肖扬, 冯煊, 陈大鹏');
INSERT INTO micropubs VALUES(11,'基于微信平台的移动教学模式研究','随着移动互联网的高速发展,移动学习已经成为人们学习的重要形式之一.探讨将微信公众平台应用于移动教学的可行性,利用微信公众平台交互功能强、普及度高、跨平台等优势,通过开发和组织微信公众资源,构建基于微信平台的移动教学新模式.本文以黄浦开大软件工程专业的“数据库原理及应用”课程为教学案例,探索基于微信平台的移动教学并予以实现,为成人教育信息化课改提供新的借鉴与思路.','2020-05-13 15:57:33.227535',0,1,'鲍筱晔, 梁正礼');
INSERT INTO micropubs VALUES(12,'基于RFID的固定资产信息管理系统设计','针对企业在固定资产管理上信息化程度低的现状,基于软件工程思想设计了功能完备的固定资产管理系统.系统由应用层、数据层、通信层、数据采集层、设备层组成.数据层基于射频识别(RFID)技术完成了对于固定资产的信息采集和信息的格式化处理.系统采用射频标签对企业的固定资产进行标识,可以为资产管理工作提供可靠、高效、实时地资产动态数据,实现资产管理工作的信息化和标准化.还对RFID定位算法进行了改进,通过引入','2020-05-13 15:57:33.505853',0,1,'章怡');
INSERT INTO micropubs VALUES(13,'食品类专业群现代学徒制建设研究','为解决当前高职教育中人才供给与企业用工需求之间的“供需错配”矛盾,武汉软件工程职业学院组建了食品类专业群,并依托《高等职业教育创新发展行动计划(2015-2018)》,选择在武汉口碑好、信誉度高的多家食品企业进行现代学徒制试点,立项建设食品药品现代学徒制英才学院,取得了初步成效.','2020-05-13 15:57:33.725555',0,1,'熊海燕, 李莹, 陈魏');
INSERT INTO micropubs VALUES(14,'集装箱综合管理系统体系结构分析与研究','本文我们将以重庆国际集装箱综合管理系统(目前已投入使用)为项目背景,通过分析自己做过的实际项目,更加深入理解软件体系结构的在实际项目中的作用和重要性.其中涉及的软件体系结构(Software Architecture)是近年来软件工程领域中的一个热点研究方法.','2020-05-13 15:57:33.891387',0,1,'吕阳');
INSERT INTO micropubs VALUES(15,'融合自注意力机制和多路金字塔卷积的软件需求聚类算法','随着软件数量的急剧增长以及种类的日益多样化,挖掘软件需求文本特征并对软件需求特征聚类,成为了软件工程领域的一大挑战.软件需求文本的聚类为软件开发过程提供了可靠的保障,同时降低了需求分析阶段的潜在风险和负面影响.然而,软件需求文本存在离散度高、噪声大和数据稀疏等特点,目前有关聚类的工作局限于单一类型的文本,鲜有考虑软件需求的功能语义.文中鉴于需求文本的特点和传统型聚类方法的局限性,提出了融合自注意力','2020-05-13 15:57:34.416680',0,1,'康雁, 崔国荣, 李浩, 杨其越, 李晋源, 王沛尧');
INSERT INTO micropubs VALUES(16,'提高软件工程专业学术型研究生培养质量实践研究','为提高软件工程专业学术型研究生培养质量,本文提出基于"双项目"导向的提高研究生综合能力的培养方法,项目分为校际学术科研项目和校企联合工程项目两类,通过项目落实,拓展研究生的专业视域,提升研究生工程实践及创新能力,缩短学习与生产之间的适应周期,对软件工程专业学术型研究生培养质量的提高具有重要意义,对其他工科学术型研究生培养具有示范作用.','2020-05-13 15:57:34.716917',0,1,'杨玉强, 韩丽艳');
INSERT INTO micropubs VALUES(17,'静态软件缺陷预测研究进展','软件缺陷预测在提高软件质量和用户满意度、降低开发成本和风险等方面起着非常重要的作用,在学术界如火如荼地展开了众多理论和实证研究,但在产业界却发现其存在着实用性差、效率低、未考虑缺陷严重等级等不足.为了查找具体原因,首先依据预测目标的不同,将静态软件缺陷预测细分为缺陷倾向性预测、缺陷的数量/分布密度预测和缺陷模块排序预测;然后从软件度量指标的筛选、测评数据资源库、缺陷预测模型的构建和缺陷预测模型的评','2020-05-13 15:57:34.894444',0,1,'吴方君');
INSERT INTO micropubs VALUES(18,'基于计算机软件工程的数据库编程技术','本文对计算机软件工程的数据库的构建方式展开研究后,也对于数据库的文件建立以及数据库的文件访问等进行了一定的讨论和研究,以此来提高计算机软件工程的数据库编程技术,进一步保证计算机软件的运行稳定性.','2020-05-13 15:57:35.127871',0,1,'吴小欣');
INSERT INTO micropubs VALUES(19,'一种基于模型和模板融合的自动代码生成方法','自动代码生成技术在软件工程中发挥着越来越重要的作用,深刻改变着软件开发过程的演进和变革,尤其是以模型驱动构架(Model Driven Architecture,MDA)指导的自动代码生成成为主导.该文梳理两大主流的代码生成技术,提出一种混合自动代码生成的方法,给出一种设计和实现的原型.该生成方法具有较高的灵活性和扩展性,能改进软件开发的过程,提高软件开发效率,具有较高的应用价值.','2020-05-13 15:57:35.513783',0,1,'王博, 华庆一, 舒新峰');
INSERT INTO micropubs VALUES(20,'DevOps中国调查研究','DevOps已提出近十年,其作为敏捷方法在完整的软件生命周期上的延伸,旨在从文化、自动化、标准化、架构以及工具支持等方面,打破开发与运维之间的壁垒,重塑软件过程,以实现在保证高质量的前提下,缩短从代码提交到产品上线之间的周期.在竞争日益激烈的市场环境下,用户对于产品服务的稳定性以及更新频率和效率的要求不断提高,DevOps在学术界和工业界的关注程度因此也不断提高.Puppet Labs在2013年','2020-05-13 15:57:35.803043',0,1,'刘博涵, 张贺, 董黎明');
INSERT INTO micropubs VALUES(21,'Java技术的应用型人才培养模式研究','从事与Java技术相关的软件研发、运营和维护是当前高校计算机专业毕业生的一个热门就业点,如何提高Java技术应用型人才质量是软件工程人才培养模式中的一个重要问题.分析了当前高校在Java技术应用型人才培养过程中存在的一些问题,从课程体系设置、教学方法改革、考核方式、师资队伍建设、校企合作等方面提出了改进措施,旨在提高软件工程专业人才培养质量.','2020-05-13 15:57:36.116194',0,1,'欧阳宏基, 葛萌, 郭新明');
INSERT INTO micropubs VALUES(22,'卓越工程师的软件工程专业人才培养模式研究','为了培养高层次应用型的一线IT软件工程师,以CDIO工程理念为指导,以社会实际需求为导向,以校企全学段深度合作培养为路径,提出了“毕业证书+行业认证”的培养要求,实施软件工程专业的“2+1+1”培养模式,设计“专业基础+专业课程+企业课程+项目实训+毕业实习”的软件工程人才培养方案,引入IT企业软件工程师,探索以项目实训形式的软件工程特色班,成立软件工程专业综合能力提升指导中心,强化教学质量监控,','2020-05-13 15:57:36.450022',0,1,'何小虎');
INSERT INTO micropubs VALUES(23,'基于动态链接库的组态软件工程授权方法','组态软件在工业自动化领域起到了至关重要的作用,然而组态软件的二次开发过程缺少重视和保护.针对以上情况,设计了基于动态链接库的组态软件工程授权方法,将组态软件特点与软件加密方法相结合,利用加密硬件作为授权载体,希望在保证系统稳定运行的前提下,防止组态监控软件非授权复制使用.将方法应用到西门子WinCC工程项目中,测试结果表明,在不同授权情况下能够及时做出响应,实现预期功能.','2020-05-13 15:57:36.825581',0,1,'王继文, 王红照');
INSERT INTO micropubs VALUES(24,'新工科背景下软件工程专业创新实践体系构建','以新工科建设为背景,在软件工程专业工程应用型人才的创新实践能力培养中,通过聚集课内外、校内外、海内外、线上线下的资源,进行课堂教学、校内实践、校外实践、国际交流、在线课程的协同培养,构建了开放的全过程实践教学体系,提高了学生的工程实践能力、创新能力和国际竞争力,开拓了学生的就业前景,为软件工程特色专业建设和人才培养提供了参考.','2020-05-13 15:57:37.078759',0,1,'林菲, 龚晓君, 马虹');
INSERT INTO micropubs VALUES(25,'云计算环境下法定计量检测信息系统应用研究','法定计量检测工作十分复杂,在计量检定单位中备受关注.要想提升计量检测工作的效率和准确性,计量检定单位可以考虑引入现代软件工程、云技术以及数据库等先进技术,研发较为完善的法定计量检测信息系统,实现检验相关工作的自动化以及智能化,实现信息共享,保障计量监督管理工作的效率,用先进技术护航,不断提高计量检定单位中检验工作的工作效率以及精准度.','2020-05-13 15:57:37.377962',0,1,'李珂');
INSERT INTO micropubs VALUES(26,'计算机专业“数字逻辑”课程教学改革','“数字逻辑”课程是计算机科学与技术、计算机网络工程、软件工程专业的一门专业必修课程.首先,分析广东理工学院计算机专业数字逻辑课程的教学现状;然后针对学校实际情况提出了数字逻辑课程教学改革的内容,包括建立完善的课程内容知识体系结构、建立教学资料库;接着罗列出了一系列的改革措施:多样化的教学模式与教学策略、多种学生成绩评定方法相结合、定期的教学经验交流会开展等.','2020-05-13 15:57:37.857803',0,1,'李小莲');
INSERT INTO micropubs VALUES(27,'试论高校敏捷服务团队及其构建','建设一支适应高校发展的行政管理服务团队,对提高高校的教书育人水平具有重要意义.在简政放权、放管结合、优化服务的大背景下,将软件工程中敏捷开发理念引入高校管理服务团队建设,构建一支主动探寻教育规律,积极参与教学改革的敏捷服务团队,将有利于不断提升管理服务质量,高质量完成教学改革,促进团队成员的自我成长.敏捷服务团队强调结果导向,提倡适应变化,重视迭代工作,其目的在于保持小微团队的自组织与自管理,促进','2020-05-13 15:57:38.164663',0,1,'张占军, 王锋, 陈诗伟');
INSERT INTO micropubs VALUES(28,'软件工程中虚拟现实的启示应用及挑战','软件工程师们都得用键盘和鼠标源与代码进行互动,而且一般都是在2D平面显示器上进行软件浏览.这种互动范式,并未很好地利用自然人类诸多的动作和洞察力的启示.虚拟现实(VR)可以更充分地利用这些启示,使新的创意成为可能,并能提高生产率,降低学习曲线和增加用户的满意度.描述了VR所提供的启示;展示了VR的益处,以及用于现场编码和代码审核的软件工程中的原型,而且讨论了未来的工作,开放性问题以及VR的挑战等等','2020-05-13 15:57:38.456701',0,1,'闵亮');
INSERT INTO micropubs VALUES(29,'敏捷开发环境中的回归测试优化技术','版本频繁交付、功能不断新增或修改、测试用例不断增多是敏捷开发环境的特点.回归测试是软件测试的一个重要组成部分,它在敏捷开发环境中更应基于环境特点进行设计.但是,传统的回归测试优化技术(测试用例优先排序或回归测试选择等)各有其优缺点,且没有考虑敏捷开发环境对测试效率的影响.测试用例优先排序技术利用设计规则对所有测试用例进行排序,以提高错误检测率,但测试集基数大,花费时间长.回归测试选择技术选择部分测','2020-05-13 15:57:38.745488',0,1,'王晓琳, 曾红卫, 林玮玮');
INSERT INTO micropubs VALUES(30,'基于风险分析的回归测试用例优先级排序','该文利用软件组件间信息流的传递过程,提出了基于风险分析的回归测试用例优先级排序算法(Risk Analysis-based Test Case Prioritization,RA-TCP).该算法针对现有的优先级排序技术未能有效利用测试用例所覆盖信息的问题,在类粒度下将软件抽象为基于信息流的类级有向网络模型,然后将每个测试用例所覆盖的类间信息传递关系用一组杠铃模型表示,结合概率风险评估方法和故障树','2020-05-13 15:57:39.078542',0,1,'于海, 杨月, 王莹, 张伟, 朱志良');
INSERT INTO micropubs VALUES(31,'基于“奖励制度”的DPoS共识机制改进','共识机制是区块链技术的核心.授权股权证明(Delegated Proof-of-Stake,DPoS)作为一种共识机制,其中每个节点都能够自主决定其信任的授权节点,从而实现快速共识验证.但DPoS机制仍然存在着节点投票不积极以及节点腐败的安全问题.针对这两个问题,文中提出了基于奖励的DPoS改进方案,投票奖励用以激励节点积极参与投票,举报奖励用以激励节点积极举报贿赂节点.Matlab仿真结果表明,','2020-05-13 15:57:39.245798',0,1,'陈梦蓉, 林英, 兰微, 单今朝');
INSERT INTO micropubs VALUES(32,'基于OBE理念的"软件工程"课程重塑','研究和分析了当前广泛开展的OBE教育方法,结合清华大学软件工程专业的软件工程教学,基于OBE理念对整个教学方案进行了改造和优化,重新设计了课程学习目标、教学内容框架、项目实践方法和课程实验环境等部分.重塑后的教学方案体现"价值塑造、能力培养、知识传授"的教学思想,以学生的课程学习效果为目标驱动,注重软件技术能力、工程实践能力以及解决复杂软件问题能力的培养,实施先进的工程教育教学方法,通过科学的评价','2020-05-13 15:57:39.402059',0,1,'刘强');
INSERT INTO micropubs VALUES(33,'基于多目标优化算法NSGA-Ⅱ推荐相似缺陷报告','在软件开发过程中,开发人员会收到用户提交的大量缺陷报告.若修复缺陷报告中问题涉及到的相同源代码文件数目超过一半,则称这些缺陷报告为相似缺陷报告.给开发人员推荐相似缺陷报告能够有效节约开发人员修复缺陷的时间.该文提出一种基于多目标优化算法NSGA-Ⅱ推荐相似缺陷报告的方法,即在推荐尽可能少的相似缺陷报告情况下,使得缺陷报告间的相似度尽可能大.为此,利用缺陷报告的摘要和描述信息,该文采用TF-IDF和','2020-05-13 15:57:39.582848',0,1,'樊田田, 许蕾, 陈林');
INSERT INTO micropubs VALUES(34,'基于卷积神经网络的代价敏感软件缺陷预测模型','基于机器学习的软件缺陷预测方法受到软件工程领域学者们的普遍关注,通过缺陷预测模型可一定程度地分析软件中的缺陷分布,以此帮助软件质量保障团队发现软件中潜在的错误并合理分配测试资源.然而,现有多数的缺陷预测方法是基于代码行数、模块依赖程度、栈引用深度等人工提取的软件特征进行缺陷预测的.此类方法未考虑到软件源码中潜在的语义特征,可能导致预测效果不理想.为了解决以上问题,文中利用卷积神经网络挖掘源码中隐含','2020-05-13 15:57:39.741515',0,1,'邱少健, 蔡子仪, 陆璐');
INSERT INTO micropubs VALUES(35,'军用软件测评实验室测评管理度量模型设计与实现?','为解决军用软件测评实验室对测评项目管理的不足,在现行软件工程相关的国际、国/军标指导下,基于软件研制能力成熟度模型技术和实用软件度量技术,设计并实现了一种军用软件测评实验室测评管理度量模型.模型建立针对质量和进度的度量体系和评价方法,以客观、量化和高效的方式实现对测试项目的定量评估,达到量化管理的目标,提升军用软件测评实验室对测评项目的管理能力.','2020-05-13 15:57:39.891113',0,1,'姜晓辉, 胡勇, 郭久武');
INSERT INTO micropubs VALUES(36,'生产建设项目水土保持“天地一体化”监管模式研究','为加强地区水土保持监测信息化工作,根据全国水土保持信息化工作要求和实际业务工作需要,结合相关技术规定要求,提出了一套生产建设项目水土保持“天地一体化”监管信息采集与管理解决方案,并在此基础上运用软件工程的方法设计了对应的生产建设项目水土保持“天地一体化”监管系统和配套的“外业辅助移动端”软件.生产建设项目水土保持“天地一体化”监管系统主要是利用遥感影像对新增地表动土开展遥感动态监测,快速、准确地获','2020-05-13 15:57:40.297108',0,1,'徐坚, 钟秀娟, 王崇任, 丁杨, 高之栋');
INSERT INTO micropubs VALUES(37,'软件工程技术在计算机系统软件开发中的应用研究','信息化时代的发展,使得我国各行业对计算机系统软件的需求力度逐渐提升.为彰显计算机系统软件在各行业中的作用效果,就应加强计算机系统软件开发力度,以满足我国各行业现代化建设要求.但是由于单一的计算机系统软件开发还存在一定缺陷,这就需要在计算机系统软件开发中应用软件工程技术,据此提升计算机系统软件开发水平.本文将概述软件工程技术,同时分析该项技术在计算机软件开发中的应用.','2020-05-13 15:57:40.458148',0,1,'卞秀运');
INSERT INTO micropubs VALUES(38,'《软件工程》教学中Android移动学习APP的应用分析','移动学习指的是在远程学习和在线学习基础上,通过利用移动终端设备,实现随时随地学习的一种方式.《软件工程》学习中,学生要提高对移动APP的关注,在教师指导下主动学习专业知识,利用APP提高学习兴趣,由此提升对教学内容的探究欲望,这样可锻炼学生对软件的开发意识及软件研究能力.','2020-05-13 15:57:40.626194',0,1,'程瑶');
INSERT INTO micropubs VALUES(39,'《软件工程》课程学生学习效果跟踪系统的设计','文章内容是一个学生学习效果跟踪系统,详细的记录了本系统的设计与实现过程及开发系统所涉及的技术和方法.系统的构架使用B/S架构,后端语言使用PHP.文中还叙述了数据库的设计思想,并通过实体关系图的方式展现了各个表的创建过程.系统使用JetBrains PhpStorm进行开发,数据库使用MySQL57,前端页面为使用Layui框架进行开发的单页应用.本系统对学生及教师的操作简单方便,教师可以发布、修','2020-05-13 15:57:40.778808',0,1,'王艳君, 李瞳');
INSERT INTO micropubs VALUES(40,'一种嵌入三维动画特效参数的数字水印算法','三维动画因其高信息量和高逼真性,广泛应用于虚拟展示、动画电影等领域.为了有效保护三维动画的知识产权,提出一种嵌入三维动画特效参数的数字水印算法.将三维动画中粒子效果和动力学效果等特效参数作为水印嵌入载体,结合满秩分解、奇异值分解和三角分解,将水印信息高效地嵌入到特效参数组成的矩阵中.由于水印是嵌入在特效参数而非场景主要特征中,所以水印具有很好的透明性.实验结果表明,该算法复杂度较低且鲁棒性较高,具','2020-05-13 15:57:41.058059',0,1,'李亚琴, 方立刚, 廖黎莉, 杨元峰');
INSERT INTO micropubs VALUES(41,'基于过程划分技术的服务组合拆分方法','针对集中式服务组合内的中心控制器瓶颈问题,提出一种基于过程划分技术的非集中式服务组合构建方法.首先,利用类型有向图对业务过程进行建模;然后,基于图转换的方法提出分组算法,根据分组算法对过程模型进行拆分;最后,根据拆分后的结果来构建非集中式服务组合.经实验测试,分组算法对模型1的耗时与单线程算法相比降低了21.4％,构建的非集中式服务组合拥有更低响应时间和更高吞吐量.实验结果表明,所提方法能有效地拆','2020-05-13 15:57:41.459349',0,1,'刘惠剑, 刘峻松, 王佳伟, 薛岗');
INSERT INTO micropubs VALUES(42,'融入兴趣区域的差分隐私轨迹数据保护方法*','轨迹数据保护方法是当前隐私保护研究领域的热点问题.现有轨迹数据隐私保护方法多数采取在所有位置点上加噪的策略,这在保护轨迹数据的同时也降低了保护后数据的可用性.为解决该问题,提出了一种融入兴趣区域的差分隐私轨迹数据保护方法.该方法首先将用户长时间停留的相近位置点集合定义为兴趣区域,将兴趣区域的中心点定义为驻留点.然后通过划定阈值的方式,从所有驻留点中挖掘出频繁驻留点,使用驻留点替代原轨迹数据中对应的','2020-05-13 15:57:41.763874',0,1,'兰微, 林英, 包聆言, 李彤, 陈梦蓉, 单今朝');
INSERT INTO micropubs VALUES(43,'软件工程实践训练设计与实践','针对现有软件工程专业教学"理论多、实践少"的现状,基于前人对软件工程专业教学的研究和清华大学软件工程课程的教学实践经验,提出了一套引入企业工程师和模拟客户参与的软件工程实践训练教学方案,并通过在南开大学软件学院的实践,论证了这项工作提出的软件工程实践教学方案的有效性.','2020-05-13 15:57:41.945742',0,1,'俞昊然, 杨博洋');
INSERT INTO micropubs VALUES(44,'面向方面记忆网络的IT产品细粒度情感分析','以用户情感需求为导向进行产品的设计和营销定位已成为研究热点,细粒度的情感挖掘可进一步提高评论分析的效率.提出一种面向方面深度记忆网络模型进行细粒度情感分析.对京东等IT产品评论数据进行爬取,应用依存句法分析方法抽取评论中的方面词,采用基于self-attention机制的深度记忆网络模型实现基于方面的细粒度情感分类.实验结果表明,面向方面深度记忆网络模型在英文数据集上的准确率相比一些经典模型有所提','2020-05-13 15:57:42.113101',0,1,'李晋源, 康雁, 杨其越, 王沛尧, 崔国荣');
INSERT INTO micropubs VALUES(45,'针对文本情感分类任务的textSE-ResNeXt集成模型','针对深度学习方法中文本表示形式单一,难以有效地利用语料之间细化的特征的缺陷,利用中英文语料的不同特性,有区别地对照抽取中英文语料的特征提出了一种新型的textSE-ResNeXt集成模型.通过PDTB语料库对语料的显式关系进行分析,从而截取语料主要情感部分,针对不同中、英文情感词典进行情感程度关系划分以此获得不同情感程度的子数据集.在textSE-ResNeXt神经网络模型中采用了动态卷积核策略,','2020-05-13 15:57:42.279864',0,1,'康雁, 李浩, 梁文韬, 宁浩宇, 霍雯');
INSERT INTO micropubs VALUES(46,'融合循环知识图谱和协同过滤电影推荐算法','推荐系统对筛选有效信息和提高信息获取效率具有重大的意义.传统的推荐系统会面临数据稀松和冷启动等问题.利用外部评分和物品内涵知识相结合,提出一种基于循环知识图谱和协同过滤的电影推荐模型——RKGE-CF.在充分考虑物品、用户、评分之间的相关性后,利用基于物品和用户的协同过滤进行Top-K推荐;将物品的外部附加数据和用户偏好数据加入知识图谱,提取实体相互之间的依赖关系,构建用户和物品之间的交互信息,以','2020-05-13 15:57:42.513884',0,1,'李浩, 张亚钏, 康雁, 杨兵, 卜荣景, 李晋源');
INSERT INTO micropubs VALUES(47,'基于主题相似性聚类的自适应文本分类','传统的文本分类方法仅使用一种模型进行分类,容易忽略不同类别特征词出现交叉的情况,影响分类性能.为提高文本分类的准确率,提出基于主题相似性聚类的文本分类算法.通过CHI和WordCount相结合的方法提取类特征词,利用K-means算法进行聚类并提取簇特征词构成簇特征词库.在此基础上,通过Adaptive Strategy算法自适应地选择fasttext、TextCNN或RCNN模型进行分类,得到最','2020-05-13 15:57:42.824689',0,1,'康雁, 杨其越, 李浩, 梁文韬, 李晋源, 崔国荣, 王沛尧');
INSERT INTO micropubs VALUES(48,'软件工程课程创新探索','软件工程课程作为一门理论内容衔接精密,知识点串接较强的专业课程,需要运用不同的教学方法和手段来促进学生创新实践教学的开展.因此创新可以从该课程的教学特点着手,重新定位课程的理念和培养目标,抓好实训在创新授课中的重要作用,进一步加强学生创新实践的能力.','2020-05-13 15:57:42.980586',0,1,'张钰莎');
INSERT INTO micropubs VALUES(49,'基于变异测试的错误定位研究进展','随着软件规模和复杂度的不断提高,软件的质量问题成为了关注的焦点,如何高效地找出软件中的错误成为一个亟需解决的问题.错误定位是软件质量保证的重要途径之一,近年来已经成为软件工程中一个非常重要的研究课题.基于变异测试的错误定位通过比较原程序和对应变异体的差异来计算每条语句的怀疑度,再由怀疑度大小进行排序,程序员根据排序逐个检查找出错误语句.汇总近7年(2012—2018)国内外的基于变异测试的错误定位','2020-05-13 15:57:43.158502',0,1,'姚毅文, 姜淑娟, 薄莉莉');
INSERT INTO micropubs VALUES(50,'基于深度学习的程序理解研究进展','程序理解通过对程序进行分析、抽象、推理从而获取程序中相关信息,在软件开发、维护、迁移等过程中起重要作用,因而得到学术界和工业界的广泛关注.传统程序理解很大程度上依赖开发人员的经验,但随着软件规模及其复杂度不断增大,完全依赖开发人员的先验知识提取程序特征既耗时耗力,又很难充分挖掘出程序中隐合特征.深度学习是一种数据驱动的端到端的方法,它根据已有数据构建深度神经网络对数据中隐含的特征进行挖掘,已经在众','2020-05-13 15:57:43.334875',0,1,'刘芳, 李戈, 胡星, 金芝');
INSERT INTO micropubs VALUES(51,'现代信息技术在高校健身健美教学中的运用——评《健身健美运动教程》','近年来,健身健美运动得到了越来越多的喜爱和关注,在高校体育课程体系中,健身健美运动课程也受到了广泛的欢迎.鉴于此,为了进一步规范与发展高校健身健美运动的课程教学,高校及教师需要不断推进健身健美教学经验的归纳总结,引入创新的教材内容、教学理念、教学手段、教学技术和教学模式来切实优化健身健美运动课程的教学效果.','2020-05-13 15:57:43.615375',0,1,'蒋晓丹');
CREATE INDEX ix_notifications_name ON notifications (name);
CREATE INDEX ix_notifications_timestamp ON notifications (timestamp);
CREATE INDEX ix_messages_timestamp ON messages (timestamp);
CREATE INDEX ix_roles_default ON roles ("default");
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_tasks_name ON tasks (name);
CREATE INDEX ix_microcons_timestamp ON microcons (timestamp);
CREATE INDEX ix_microcons_title ON microcons (title);
CREATE INDEX ix_tags_content ON tags (content);
CREATE INDEX ix_comments_timestamp ON comments (timestamp);
CREATE INDEX ix_micropubs_timestamp ON micropubs (timestamp);
CREATE INDEX ix_micropubs_title ON micropubs (title);
COMMIT;
