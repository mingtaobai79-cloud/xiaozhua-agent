# Metadata artifact evidence — 5.3.358

- Source JAR: `<MAVEN_REPO>/com/seeyon/boot-starter-metadata/5.3.358/boot-starter-metadata-5.3.358.jar`
- JAR SHA-256: `926c28022df0502bfd988df0cf31417fb70e0603af3d39df98015e65a7028431`

## Confirmed static facts

- `MetadataModifyAppService.modifyEntityAttribute(SingleRequest<EntityAttributeModifyDto>)` delegates to `MetadataService.modifyEntityAttribute(EntityAttributeModifyDto)`.
- `MetadataModifyAppService.coverAllModifyEntityAttribute(SingleRequest<List<EntityAttributeModifyDto>>)` delegates to `MetadataService.coverAllModifyEntityAttribute(List<EntityAttributeModifyDto>)`.
- `MetadataCreateAppService` exposes `createAllEntityMetadata(SingleRequest<ServiceEntityMetadataDto>)` and other metadata creation operations.
- `MetadataService` has `MetadataTypeEnum.Entity`, `createMetadata`, `createJsonMetadata`, `selectOrigMetadataMap`, `selectEntityMetadata...`, RedisTemplate fields/operations, FileService, storage-key and MD5-key utilities, and `onChange`/async storage methods in bytecode references.
- The artifact therefore confirms a metadata subsystem with Redis/cache plus file-storage paths and entity/attribute metadata modification APIs.

## Boundary

This artifact is `VERIFIED_STATIC_BYTECODE` for the metadata subsystem API/dependency shape. It is not proof that the specific UDC GraphQL mutation `udcEntityPost` invokes these methods. The resolver mapping from GraphQL fieldType to this service, concrete UDC EntityAppService implementation, exact storage key/value, and generated source remain UNVERIFIED.

## `MetadataService.javap.txt`
```text
Classfile /<XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/metadata-5.3.358/MetadataService.class
  Compiled from "MetadataService.java"
     #1 = Fieldref           #120.#1224   // com/seeyon/ctp/metadata/domain/service/MetadataService.appServiceReliableInvoker:Lcom/seeyon/boot/starter/proxy/appservice/AppServiceReliableInvoker;
     #2 = Methodref          #120.#1225   // com/seeyon/ctp/metadata/domain/service/MetadataService.upgrade:(Ljava/util/Map;Ljava/util/List;)V
     #3 = Methodref          #120.#1226   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectMultiVersionStarterMetadataMap:(Ljava/lang/String;)Ljava/util/Map;
     #4 = Methodref          #120.#1227   // com/seeyon/ctp/metadata/domain/service/MetadataService.multiVersionStarterUpgrade:(Ljava/lang/String;)V
     #5 = Fieldref           #120.#1228   // com/seeyon/ctp/metadata/domain/service/MetadataService.fileService:Lcom/seeyon/boot/starter/file/FileService;
     #6 = Methodref          #120.#1229   // com/seeyon/ctp/metadata/domain/service/MetadataService.callServer:(Ljava/lang/String;Ljava/lang/Object;)Ljava/lang/Object;
     #7 = Fieldref           #120.#1230   // com/seeyon/ctp/metadata/domain/service/MetadataService.log:Lorg/slf4j/Logger;
     #8 = Fieldref           #120.#1231   // com/seeyon/ctp/metadata/domain/service/MetadataService.ignoreCheckServiceMetadata:Z
     #9 = Fieldref           #120.#1232   // com/seeyon/ctp/metadata/domain/service/MetadataService.STARTER_NAME_SET:Ljava/util/Set;
    #10 = Methodref          #120.#1233   // com/seeyon/ctp/metadata/domain/service/MetadataService.loadMetadataFromStorage:(Ljava/lang/String;Z)Ljava/util/Map;
    #11 = Fieldref           #120.#1234   // com/seeyon/ctp/metadata/domain/service/MetadataService.metadataRedisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
    #12 = Fieldref           #120.#1235   // com/seeyon/ctp/metadata/domain/service/MetadataService.MD5CACHE:Ljava/util/Map;
    #13 = Methodref          #120.#1236   // com/seeyon/ctp/metadata/domain/service/MetadataService.getOldVersionJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    #14 = Methodref          #120.#1237   // com/seeyon/ctp/metadata/domain/service/MetadataService.getMetadataStrFromStorage:(Ljava/lang/String;)Ljava/lang/String;
    #16 = Fieldref           #120.#1239   // com/seeyon/ctp/metadata/domain/service/MetadataService.serviceCacheTime:Ljava/lang/String;
    #18 = Fieldref           #120.#1241   // com/seeyon/ctp/metadata/domain/service/MetadataService.serviceRedisChange:Ljava/lang/String;
    #19 = Class              #1242        // org/springframework/data/redis/core/RedisTemplate
    #20 = Methodref          #19.#1238    // org/springframework/data/redis/core/RedisTemplate."<init>":()V
    #21 = Methodref          #19.#1243    // org/springframework/data/redis/core/RedisTemplate.setConnectionFactory:(Lorg/springframework/data/redis/connection/RedisConnectionFactory;)V
    #22 = Class              #1244        // org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer
    #24 = Methodref          #22.#1246    // org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer."<init>":(Ljava/lang/Class;)V
    #25 = Fieldref           #120.#1247   // com/seeyon/ctp/metadata/domain/service/MetadataService.jackson2JsonRedisSerializer:Lorg/springframework/data/redis/serializer/Jackson2JsonRedisSerializer;
    #42 = Methodref          #22.#1271    // org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer.setObjectMapper:(Lcom/fasterxml/jackson/databind/ObjectMapper;)V
    #43 = Class              #1272        // org/springframework/data/redis/serializer/StringRedisSerializer
    #44 = Methodref          #43.#1238    // org/springframework/data/redis/serializer/StringRedisSerializer."<init>":()V
    #45 = Methodref          #19.#1273    // org/springframework/data/redis/core/RedisTemplate.setKeySerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
    #46 = Methodref          #19.#1274    // org/springframework/data/redis/core/RedisTemplate.setValueSerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
    #47 = Methodref          #19.#1275    // org/springframework/data/redis/core/RedisTemplate.setHashKeySerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
    #48 = Methodref          #19.#1276    // org/springframework/data/redis/core/RedisTemplate.setHashValueSerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
    #49 = Methodref          #19.#1277    // org/springframework/data/redis/core/RedisTemplate.afterPropertiesSet:()V
    #65 = Fieldref           #120.#1300   // com/seeyon/ctp/metadata/domain/service/MetadataService.CACHE:Lcom/google/common/cache/Cache;
    #66 = Fieldref           #120.#1301   // com/seeyon/ctp/metadata/domain/service/MetadataService.SERVICE_CACHE:Lcom/google/common/cache/Cache;
    #67 = Fieldref           #120.#1302   // com/seeyon/ctp/metadata/domain/service/MetadataService.JSON_CACHE:Lcom/google/common/cache/Cache;
    #74 = Fieldref           #120.#1306   // com/seeyon/ctp/metadata/domain/service/MetadataService.LOAD_FROM_STORAGE_FAIL_KEY_CACHE:Lcom/google/common/cache/Cache;
    #75 = Methodref          #120.#1307   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectServiceMetadataByName:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
    #87 = Methodref          #1318.#1319  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.metadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
    #88 = Methodref          #1318.#1320  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.md5Rediskey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
    #92 = Methodref          #120.#1325   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectMultiVersionServiceMetadataList:(Ljava/lang/String;)Ljava/util/List;
   #100 = Methodref          #1318.#1336  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.multiVersionMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #101 = Methodref          #1318.#1337  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.multiVersionMd5Rediskey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #102 = Methodref          #120.#1338   // com/seeyon/ctp/metadata/domain/service/MetadataService.deleteFromStorage:(Ljava/util/List;)V
   #103 = Methodref          #19.#1339    // org/springframework/data/redis/core/RedisTemplate.delete:(Ljava/util/Collection;)Ljava/lang/Long;
   #107 = Methodref          #120.#1343   // com/seeyon/ctp/metadata/domain/service/MetadataService.removeMetadata:(Ljava/lang/String;Ljava/lang/String;Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;)Z
   #108 = Methodref          #1318.#1344  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.getMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #109 = Methodref          #1318.#1345  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.getMetadataMd5RedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #110 = Fieldref           #1316.#1346  // com/seeyon/ctp/metadata/enums/MetadataTypeEnum.Entity:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
   #112 = Methodref          #1318.#1348  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.tenantMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
   #113 = Methodref          #1318.#1349  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.tenantMD5RedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
   #114 = Methodref          #19.#1350    // org/springframework/data/redis/core/RedisTemplate.opsForHash:()Lorg/springframework/data/redis/core/HashOperations;
   #116 = InterfaceMethodref #1352.#1353  // org/springframework/data/redis/core/HashOperations.delete:(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Long;
   #117 = Methodref          #19.#1354    // org/springframework/data/redis/core/RedisTemplate.opsForValue:()Lorg/springframework/data/redis/core/ValueOperations;
   #124 = InterfaceMethodref #1360.#1361  // org/springframework/data/redis/core/ValueOperations.set:(Ljava/lang/Object;Ljava/lang/Object;JLjava/util/concurrent/TimeUnit;)V
   #125 = Methodref          #120.#1362   // com/seeyon/ctp/metadata/domain/service/MetadataService.redis2storage:(Ljava/lang/String;)V
   #127 = Methodref          #1318.#1364  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.starterMetadataRedisKey:()Ljava/lang/String;
   #128 = InterfaceMethodref #1352.#1365  // org/springframework/data/redis/core/HashOperations.size:(Ljava/lang/Object;)Ljava/lang/Long;
   #130 = Methodref          #120.#1368   // com/seeyon/ctp/metadata/domain/service/MetadataService.loadStarterMetadataFromStorage:()Ljava/util/Map;
   #131 = InterfaceMethodref #1352.#1369  // org/springframework/data/redis/core/HashOperations.entries:(Ljava/lang/Object;)Ljava/util/Map;
   #142 = Methodref          #120.#1379   // com/seeyon/ctp/metadata/domain/service/MetadataService.needUpdate:(Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;)Z
   #144 = Methodref          #120.#1381   // com/seeyon/ctp/metadata/domain/service/MetadataService.createMultiVersionStaterMetadata:(Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;)V
   #146 = InterfaceMethodref #1352.#1383  // org/springframework/data/redis/core/HashOperations.putAll:(Ljava/lang/Object;Ljava/util/Map;)V
   #148 = Methodref          #120.#1386   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectMultiVersionStarterMetadataList:(Ljava/lang/String;)Ljava/util/List;
   #151 = Methodref          #1318.#1389  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.starterMultiVersionRedisKey:(Ljava/lang/String;)Ljava/lang/String;
   #152 = Methodref          #19.#1390    // org/springframework/data/redis/core/RedisTemplate.delete:(Ljava/lang/Object;)Ljava/lang/Boolean;
   #153 = InterfaceMethodref #1352.#1391  // org/springframework/data/redis/core/HashOperations.put:(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)V
   #162 = Methodref          #1318.#1399  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.serviceMultiVersionRedisKey:(Ljava/lang/String;)Ljava/lang/String;
   #164 = Methodref          #19.#1401    // org/springframework/data/redis/core/RedisTemplate.expire:(Ljava/lang/Object;JLjava/util/concurrent/TimeUnit;)Ljava/lang/Boolean;
   #165 = Methodref          #120.#1402   // com/seeyon/ctp/metadata/domain/service/MetadataService.asyncSave2Storage:(Ljava/lang/String;Ljava/util/Map;)V
   #167 = Methodref          #120.#1403   // com/seeyon/ctp/metadata/domain/service/MetadataService.createJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZLjava/io/InputStream;)Z
   #168 = Methodref          #1318.#1404  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.multiVersionJsonMetadataStorageKey:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Z)Ljava/lang/String;
   #169 = Methodref          #120.#1405   // com/seeyon/ctp/metadata/domain/service/MetadataService.syncSave2Storage:(Ljava/lang/String;Ljava/io/InputStream;)V
   #172 = Methodref          #1318.#1408  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.jsonMetadataStorageKey:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #176 = Methodref          #120.#1413   // com/seeyon/ctp/metadata/domain/service/MetadataService.createMultiVersionJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)Z
   #177 = Methodref          #1318.#1414  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.jsonMetadataVersionRediskey:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #180 = Methodref          #120.#1418   // com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;ZZ)Z
   #184 = Methodref          #120.#1422   // com/seeyon/ctp/metadata/domain/service/MetadataService.redisKeyToStorageKey:(Ljava/lang/String;)Ljava/lang/String;
   #185 = Methodref          #1423.#1424  // com/seeyon/boot/starter/file/FileService.exist:(Ljava/lang/String;)Z
   #187 = Fieldref           #1316.#1426  // com/seeyon/ctp/metadata/enums/MetadataTypeEnum.RestApi:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
   #196 = InterfaceMethodref #1360.#1378  // org/springframework/data/redis/core/ValueOperations.get:(Ljava/lang/Object;)Ljava/lang/Object;
   #201 = Methodref          #120.#1440   // com/seeyon/ctp/metadata/domain/service/MetadataService.onChange:(Ljava/lang/String;Ljava/lang/String;Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/util/Map;)V
   #203 = Methodref          #120.#1442   // com/seeyon/ctp/metadata/domain/service/MetadataService.createMultiVersionMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)V
   #210 = Fieldref           #120.#1449   // com/seeyon/ctp/metadata/domain/service/MetadataService.lockFactory:Lcom/seeyon/boot/starter/lock/DistributedLockFactory;
   #214 = Methodref          #120.#1455   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectTenantMetadataForMap:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/util/Map;
   #216 = Methodref          #120.#1457   // com/seeyon/ctp/metadata/domain/service/MetadataService.syncSave2Storage:(Ljava/lang/String;Ljava/util/Map;)V
   #223 = Methodref          #120.#1465   // com/seeyon/ctp/metadata/domain/service/MetadataService.createServiceMetadata:(Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;Z)Z
   #226 = Methodref          #1318.#1469  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.serviceMetadataRedisKey:()Ljava/lang/String;
   #228 = Methodref          #120.#1471   // com/seeyon/ctp/metadata/domain/service/MetadataService.createMultiVersionServiceMetadata:(Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;)V
   #230 = Methodref          #120.#1473   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectMultiVersionServiceMetadataMap:(Ljava/lang/String;)Ljava/util/Map;
   #241 = Methodref          #120.#1482   // com/seeyon/ctp/metadata/domain/service/MetadataService.select:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;ZZ)Ljava/util/List;
   #242 = Methodref          #120.#1483   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectForMap:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;ZZ)Ljava/util/Map;
   #250 = Methodref          #120.#1487   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectByFullNames:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/List;ZZ)Ljava/util/List;
   #260 = Methodref          #120.#1491   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectByFullName:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZZ)Ljava/lang/Object;
   #267 = InterfaceMethodref #1360.#1497  // org/springframework/data/redis/core/ValueOperations.multiGet:(Ljava/util/Collection;)Ljava/util/List;
   #275 = String             #1508        // entity-metadata
   #278 = Methodref          #120.#1511   // com/seeyon/ctp/metadata/domain/service/MetadataService.getAppName:(Ljava/lang/String;)Ljava/lang/String;
   #283 = Methodref          #120.#1516   // com/seeyon/ctp/metadata/domain/service/MetadataService.isSystemAdmin:()Z
   #285 = Methodref          #120.#1518   // com/seeyon/ctp/metadata/domain/service/MetadataService.useLocalCache:(Ljava/lang/String;Ljava/lang/String;)Z
   #288 = Methodref          #120.#1521   // com/seeyon/ctp/metadata/domain/service/MetadataService.localeCacheKey:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
   #295 = Methodref          #120.#1528   // com/seeyon/ctp/metadata/domain/service/MetadataService.mergeModifyAttributes:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/util/Map;)V
   #298 = Methodref          #120.#1530   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectModifiedEntityAttributes:(Ljava/lang/String;)Ljava/util/Map;
   #319 = Fieldref           #120.#1553   // com/seeyon/ctp/metadata/domain/service/MetadataService.TENANT_REDIS_KEY_EXPIRE:Lcom/google/common/cache/Cache;
   #322 = Methodref          #120.#1556   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectDtoMetadataByEntity:(Ljava/lang/String;Ljava/lang/String;Ljava/util/List;ZZ)Ljava/util/List;
   #324 = Methodref          #120.#1557   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectDtoMetadataByEntity:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZZ)Lcom/seeyon/ctp/metadata/dto/DtoMetadataDto;
   #338 = Methodref          #120.#1567   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectServiceMetadataByAppNames:(Ljava/util/List;)Ljava/util/List;
   #341 = Methodref          #120.#1569   // com/seeyon/ctp/metadata/domain/service/MetadataService.getNewVersionServiceFromStorage:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
   #346 = Methodref          #120.#1572   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectServiceMetadataByName:(Ljava/lang/String;Z)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
   #347 = Methodref          #120.#1573   // com/seeyon/ctp/metadata/domain/service/MetadataService.updateServiceListCache:()V
   #348 = InterfaceMethodref #1352.#1574  // org/springframework/data/redis/core/HashOperations.get:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
   #349 = Methodref          #120.#1575   // com/seeyon/ctp/metadata/domain/service/MetadataService.checkMavenInfo:(Lcom/seeyon/ctp/metadata/dto/model/MavenInfoDto;Lcom/seeyon/ctp/metadata/dto/model/MavenInfoDto;)I
   #350 = Methodref          #120.#1576   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectServiceMetadataMap:()Ljava/util/Map;
   #351 = Methodref          #120.#1577   // com/seeyon/ctp/metadata/domain/service/MetadataService.getNewVersionStarterFromStorage:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
   #355 = Methodref          #120.#1582   // com/seeyon/ctp/metadata/domain/service/MetadataService.getNewVersion:(Ljava/util/Set;)Ljava/lang/String;
   #366 = Methodref          #120.#1591   // com/seeyon/ctp/metadata/domain/service/MetadataService.getNewVersionServiceFromStorage:(Ljava/util/Map;)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
   #367 = Methodref          #120.#1592   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectStarterMetadataMap:()Ljava/util/Map;
   #371 = Methodref          #1423.#1596  // com/seeyon/boot/starter/file/FileService.getStorageType:()Ljava/lang/String;
   #375 = Methodref          #120.#1600   // com/seeyon/ctp/metadata/domain/service/MetadataService.downloadStr:(Ljava/lang/String;)Ljava/lang/String;
   #377 = Methodref          #22.#1602    // org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer.deserialize:([B)Ljava/lang/Object;
   #381 = Methodref          #120.#1606   // com/seeyon/ctp/metadata/domain/service/MetadataService.getServiceMetadataCache:()Ljava/util/Map;
   #388 = Methodref          #120.#1609   // com/seeyon/ctp/metadata/domain/service/MetadataService.getNearVersion:(Ljava/util/Set;Ljava/lang/String;)Ljava/lang/String;
   #389 = Methodref          #120.#1610   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectStarterMetadataByName:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
   #394 = Methodref          #1318.#1614  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.entityAttributeModifyRedisKey:(Ljava/lang/String;)Ljava/lang/String;
   #395 = Methodref          #1318.#1615  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.entityAttributeModifyHashKey:(Lcom/seeyon/ctp/metadata/dto/request/EntityAttributeModifyDto;)Ljava/lang/String;
   #407 = Methodref          #120.#1627   // com/seeyon/ctp/metadata/domain/service/MetadataService.createAggMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;)V
   #413 = Methodref          #22.#1633    // org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer.serialize:(Ljava/lang/Object;)[B
   #415 = Methodref          #120.#1635   // com/seeyon/ctp/metadata/domain/service/MetadataService.syncSave2Storage:(Ljava/lang/String;Ljava/lang/String;)V
   #417 = String             #1637        // SystemEnvironment.isLocalRun() || SystemEnvironment.isLocal(),�����ϴ�Ԫ�����ļ�,redisKey:{}
   #418 = Methodref          #120.#1638   // com/seeyon/ctp/metadata/domain/service/MetadataService.needSaveStorage:(Ljava/lang/String;)Z
   #419 = Methodref          #1423.#1639  // com/seeyon/boot/starter/file/FileService.uploadForPublicNoDB:(Ljava/lang/String;Ljava/lang/String;)Lcom/seeyon/boot/starter/file/dto/response/UploadResultDto;
   #420 = String             #1640        // SystemEnvironment.isLocalRun() || SystemEnvironment.isLocal(),�����ϴ�����Ԫ�����ļ�,redisKey:{}
   #421 = Methodref          #1423.#1641  // com/seeyon/boot/starter/file/FileService.uploadForPublicNoDB:(Ljava/io/InputStream;Ljava/lang/String;)Lcom/seeyon/boot/starter/file/dto/response/UploadResultDto;
   #453 = Methodref          #120.#1671   // com/seeyon/ctp/metadata/domain/service/MetadataService.scan:(Z)V
   #457 = Methodref          #120.#1675   // com/seeyon/ctp/metadata/domain/service/MetadataService.downgradeServiceMetadata:(Ljava/lang/String;Z)Z
   #460 = Methodref          #19.#1678    // org/springframework/data/redis/core/RedisTemplate.keys:(Ljava/lang/Object;)Ljava/util/Set;
   #469 = Methodref          #1318.#1686  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.serviceMetadataChangeRedisKey:()Ljava/lang/String;
   #470 = Fieldref           #120.#1687   // com/seeyon/ctp/metadata/domain/service/MetadataService.redisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
   #477 = Fieldref           #120.#1693   // com/seeyon/ctp/metadata/domain/service/MetadataService.STARTED:Z
   #479 = Methodref          #120.#1695   // com/seeyon/ctp/metadata/domain/service/MetadataService.currentService:()Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
   #481 = InterfaceMethodref #1352.#1678  // org/springframework/data/redis/core/HashOperations.keys:(Ljava/lang/Object;)Ljava/util/Set;
   #487 = Methodref          #1423.#1702  // com/seeyon/boot/starter/file/FileService.downloadForPublic:(Ljava/lang/String;)Ljava/io/InputStream;
   #490 = String             #1706        // ͨ��MetadataStr�����л�Ԫ����ʧ��,RedisKey:{}
   #491 = Methodref          #1423.#1707  // com/seeyon/boot/starter/file/FileService.download:(Ljava/lang/String;)Ljava/io/InputStream;
   #498 = String             #1712        // �Ӷ���洢��ȡԪ�����쳣,storageKey:{},Message:{}
   #500 = String             #1714        // ���ļ��洢��ȡԪ����ʧ��,RedisKey:{}
   #503 = Methodref          #120.#1717   // com/seeyon/ctp/metadata/domain/service/MetadataService.upgrade:(Ljava/lang/String;Ljava/util/List;)V
   #504 = Methodref          #120.#1718   // com/seeyon/ctp/metadata/domain/service/MetadataService.multiVersionServiceUpgrade:(Ljava/lang/String;)V
   #525 = Methodref          #120.#1736   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectServiceMetadataList:()Ljava/util/List;
   #528 = Methodref          #120.#1738   // com/seeyon/ctp/metadata/domain/service/MetadataService.upgradeByAppName:(Ljava/lang/String;Ljava/util/List;)V
   #530 = Methodref          #120.#1740   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectStarterMetadataList:()Ljava/util/List;
   #545 = Methodref          #120.#1754   // com/seeyon/ctp/metadata/domain/service/MetadataService.upgradeKey:(Ljava/lang/String;Ljava/lang/String;Ljava/util/List;)V
   #558 = Methodref          #120.#1765   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectEntityListByAgg:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Ljava/util/List;
   #559 = Methodref          #120.#1766   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectReferMetadataByEntity:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Ljava/util/List;
   #566 = Methodref          #120.#1770   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectReferMetadataByEntity:(Lcom/seeyon/ctp/metadata/dto/request/SearchReferByFullNamesDto;)Ljava/util/List;
   #571 = Methodref          #120.#1772   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectEntityRelationDtoMetadata:(Lcom/seeyon/ctp/metadata/dto/request/SearchMetadataDto;)Ljava/util/List;
   #577 = Methodref          #120.#1775   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectDtoMetadataByEntity:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNamesDto;)Ljava/util/List;
   #578 = Methodref          #120.#1776   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectDtoMetadataByEntity:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Lcom/seeyon/ctp/metadata/dto/DtoMetadataDto;
   #579 = Methodref          #120.#1777   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectAggDtoMetadatas:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNamesDto;)Ljava/util/List;
   #580 = Methodref          #120.#1778   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectAggDtoMetadata:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Lcom/seeyon/ctp/metadata/dto/AggDtoMetadataDto;
   #583 = Methodref          #120.#1780   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectAggEntityMetadataByAppName:(Lcom/seeyon/ctp/metadata/dto/request/SearchMetadataDto;)Ljava/util/List;
   #584 = Methodref          #120.#1781   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectAggEntityMetadataByFullName:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Lcom/seeyon/ctp/metadata/dto/AggEntityMetadataDto;
   #585 = Methodref          #120.#1782   // com/seeyon/ctp/metadata/domain/service/MetadataService.selectAggEntityMetadataByFullNames:(Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNamesDto;)Ljava/util/List;
   #594 = Utf8               REDIS_EXPIRE_TIME
   #597 = Utf8               metadataRedisTemplate
   #598 = Utf8               Lorg/springframework/data/redis/core/RedisTemplate;
   #599 = Utf8               redisTemplate
   #602 = Utf8               fileService
   #603 = Utf8               Lcom/seeyon/boot/starter/file/FileService;
   #604 = Utf8               jackson2JsonRedisSerializer
   #605 = Utf8               Lorg/springframework/data/redis/serializer/Jackson2JsonRedisSerializer;
   #607 = Utf8               Lorg/springframework/data/redis/serializer/Jackson2JsonRedisSerializer<Ljava/lang/Object;>;
   #618 = Utf8               TENANT_REDIS_KEY_EXPIRE
   #619 = Utf8               LOAD_FROM_STORAGE_FAIL_KEY_CACHE
   #629 = Utf8               serviceRedisChange
   #634 = Utf8               (Lorg/springframework/data/redis/connection/RedisConnectionFactory;)V
   #641 = Utf8               redisConnectionFactory
   #642 = Utf8               Lorg/springframework/data/redis/connection/RedisConnectionFactory;
   #645 = Utf8               stringRedisSerializer
   #646 = Utf8               Lorg/springframework/data/redis/serializer/StringRedisSerializer;
   #653 = Class              #1788        // org/springframework/data/redis/connection/RedisConnectionFactory
   #655 = Class              #1272        // org/springframework/data/redis/serializer/StringRedisSerializer
   #666 = Utf8               redisKeys
   #668 = Utf8               storageKeys
   #688 = Utf8               redisKey
   #689 = Utf8               md5RedisKey
   #725 = Utf8               serviceMultiVersionRedisKey
   #742 = Utf8               createJsonMetadata
   #750 = Utf8               multiVersionStorageKey
   #754 = Utf8               storageKey
   #760 = Utf8               createMetadata
   #763 = Utf8               storageExist
   #769 = Utf8               multiVersionRestApiFileName
   #776 = Utf8               storageExistForStarter
   #798 = Utf8               finalJsonMetadataStorageKey
   #801 = Utf8               jsonMetadataStorageKey
   #802 = Utf8               jsonMetadataVersionRediskey
   #893 = Utf8               tenantMetadataRedisKey
   #944 = Utf8               redisObj
   #951 = Utf8               getNewVersionStarterFromStorage
   #962 = Utf8               getNewVersionServiceFromStorage
   #974 = Utf8               selectServiceMetadataFromRedis
   #976 = Utf8               serviceMetadataRedisKey
   #978 = Utf8               selectOldServiceMetadataFromStorage
  #1005 = Utf8               modifyEntityAttribute
  #1008 = Utf8               modifyRedisKey
  #1009 = Utf8               coverAllModifyEntityAttribute
  #1029 = Utf8               md5Rediskey
  #1053 = Utf8               redisMd5
  #1055 = Utf8               redisKeyToStorageKey
  #1057 = Utf8               needSaveStorage
  #1058 = Utf8               syncSave2Storage
  #1064 = Utf8               redis2storage
  #1067 = Utf8               asyncSave2Storage
  #1079 = Utf8               redisKeyPattern
  #1088 = Utf8               serviceMetadataChangeRedisKey
  #1092 = Utf8               starterMetadataRedisKey
  #1097 = Utf8               deleteFromStorage
  #1100 = Utf8               saveServiceMetadataToStorage
  #1103 = Utf8               getServiceMetadataFromStorage
  #1106 = Utf8               loadStarterMetadataFromStorage
  #1111 = Utf8               getMetadataStrFromStorage
  #1112 = Utf8               noEnvRedisKey
  #1113 = Utf8               loadMetadataFromStorage
  #1199 = Utf8               (Lcom/seeyon/ctp/metadata/domain/service/MetadataService;)Lorg/springframework/data/redis/core/RedisTemplate;
  #1211 = Utf8               (Lcom/seeyon/ctp/metadata/domain/service/MetadataService;)Lcom/seeyon/boot/starter/file/FileService;
  #1222 = Utf8               MetadataService.java
  #1228 = NameAndType        #602:#603    // fileService:Lcom/seeyon/boot/starter/file/FileService;
  #1233 = NameAndType        #1113:#1114  // loadMetadataFromStorage:(Ljava/lang/String;Z)Ljava/util/Map;
  #1234 = NameAndType        #597:#598    // metadataRedisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
  #1237 = NameAndType        #1111:#856   // getMetadataStrFromStorage:(Ljava/lang/String;)Ljava/lang/String;
  #1241 = NameAndType        #629:#628    // serviceRedisChange:Ljava/lang/String;
  #1242 = Utf8               org/springframework/data/redis/core/RedisTemplate
  #1243 = NameAndType        #1800:#634   // setConnectionFactory:(Lorg/springframework/data/redis/connection/RedisConnectionFactory;)V
  #1244 = Utf8               org/springframework/data/redis/serializer/Jackson2JsonRedisSerializer
  #1247 = NameAndType        #604:#605    // jackson2JsonRedisSerializer:Lorg/springframework/data/redis/serializer/Jackson2JsonRedisSerializer;
  #1272 = Utf8               org/springframework/data/redis/serializer/StringRedisSerializer
  #1273 = NameAndType        #1843:#1844  // setKeySerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
  #1274 = NameAndType        #1845:#1844  // setValueSerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
  #1275 = NameAndType        #1846:#1844  // setHashKeySerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
  #1276 = NameAndType        #1847:#1844  // setHashValueSerializer:(Lorg/springframework/data/redis/serializer/RedisSerializer;)V
  #1306 = NameAndType        #619:#612    // LOAD_FROM_STORAGE_FAIL_KEY_CACHE:Lcom/google/common/cache/Cache;
  #1318 = Class              #1887        // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils
  #1319 = NameAndType        #1888:#1889  // metadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
  #1320 = NameAndType        #1029:#1889  // md5Rediskey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
  #1336 = NameAndType        #1908:#1909  // multiVersionMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1337 = NameAndType        #1910:#1909  // multiVersionMd5Rediskey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1338 = NameAndType        #1097:#1098  // deleteFromStorage:(Ljava/util/List;)V
  #1344 = NameAndType        #1915:#1909  // getMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1345 = NameAndType        #1916:#1909  // getMetadataMd5RedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1348 = NameAndType        #893:#1889   // tenantMetadataRedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
  #1349 = NameAndType        #1919:#1889  // tenantMD5RedisKey:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;)Ljava/lang/String;
  #1350 = NameAndType        #1920:#1921  // opsForHash:()Lorg/springframework/data/redis/core/HashOperations;
  #1352 = Class              #1924        // org/springframework/data/redis/core/HashOperations
  #1354 = NameAndType        #1926:#1927  // opsForValue:()Lorg/springframework/data/redis/core/ValueOperations;
  #1360 = Class              #1933        // org/springframework/data/redis/core/ValueOperations
  #1362 = NameAndType        #1064:#1065  // redis2storage:(Ljava/lang/String;)V
  #1364 = NameAndType        #1092:#1883  // starterMetadataRedisKey:()Ljava/lang/String;
  #1368 = NameAndType        #1106:#975   // loadStarterMetadataFromStorage:()Ljava/util/Map;
  #1389 = NameAndType        #1954:#856   // starterMultiVersionRedisKey:(Ljava/lang/String;)Ljava/lang/String;
  #1399 = NameAndType        #725:#856    // serviceMultiVersionRedisKey:(Ljava/lang/String;)Ljava/lang/String;
  #1402 = NameAndType        #1067:#1059  // asyncSave2Storage:(Ljava/lang/String;Ljava/util/Map;)V
  #1403 = NameAndType        #742:#753    // createJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZLjava/io/InputStream;)Z
  #1404 = NameAndType        #1965:#1966  // multiVersionJsonMetadataStorageKey:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Z)Ljava/lang/String;
  #1405 = NameAndType        #1058:#1063  // syncSave2Storage:(Ljava/lang/String;Ljava/io/InputStream;)V
  #1408 = NameAndType        #801:#847    // jsonMetadataStorageKey:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1414 = NameAndType        #802:#847    // jsonMetadataVersionRediskey:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
  #1418 = NameAndType        #760:#778    // createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;ZZ)Z
  #1422 = NameAndType        #1055:#856   // redisKeyToStorageKey:(Ljava/lang/String;)Ljava/lang/String;
  #1423 = Class              #1978        // com/seeyon/boot/starter/file/FileService
  #1426 = NameAndType        #1981:#662   // RestApi:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
  #1440 = NameAndType        #1049:#1050  // onChange:(Ljava/lang/String;Ljava/lang/String;Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/util/Map;)V
  #1457 = NameAndType        #1058:#1059  // syncSave2Storage:(Ljava/lang/String;Ljava/util/Map;)V
  #1469 = NameAndType        #976:#1883   // serviceMetadataRedisKey:()Ljava/lang/String;
  #1508 = Utf8               entity-metadata
  #1553 = NameAndType        #618:#612    // TENANT_REDIS_KEY_EXPIRE:Lcom/google/common/cache/Cache;
  #1569 = NameAndType        #962:#940    // getNewVersionServiceFromStorage:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
  #1577 = NameAndType        #951:#950    // getNewVersionStarterFromStorage:(Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
  #1591 = NameAndType        #962:#964    // getNewVersionServiceFromStorage:(Ljava/util/Map;)Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;
  #1596 = NameAndType        #2078:#1883  // getStorageType:()Ljava/lang/String;
  #1614 = NameAndType        #2088:#856   // entityAttributeModifyRedisKey:(Ljava/lang/String;)Ljava/lang/String;
  #1635 = NameAndType        #1058:#1062  // syncSave2Storage:(Ljava/lang/String;Ljava/lang/String;)V
  #1637 = Utf8               SystemEnvironment.isLocalRun() || SystemEnvironment.isLocal(),�����ϴ�Ԫ�����ļ�,redisKey:{}
  #1638 = NameAndType        #1057:#658   // needSaveStorage:(Ljava/lang/String;)Z
  #1640 = Utf8               SystemEnvironment.isLocalRun() || SystemEnvironment.isLocal(),�����ϴ�����Ԫ�����ļ�,redisKey:{}
  #1686 = NameAndType        #1088:#1883  // serviceMetadataChangeRedisKey:()Ljava/lang/String;
  #1687 = NameAndType        #599:#598    // redisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
  #1706 = Utf8               ͨ��MetadataStr�����л�Ԫ����ʧ��,RedisKey:{}
  #1712 = Utf8               �Ӷ���洢��ȡԪ�����쳣,storageKey:{},Message:{}
  #1714 = Utf8               ���ļ��洢��ȡԪ����ʧ��,RedisKey:{}
  #1788 = Utf8               org/springframework/data/redis/connection/RedisConnectionFactory
  #1844 = Utf8               (Lorg/springframework/data/redis/serializer/RedisSerializer;)V
  #1887 = Utf8               com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils
  #1888 = Utf8               metadataRedisKey
  #1908 = Utf8               multiVersionMetadataRedisKey
  #1910 = Utf8               multiVersionMd5Rediskey
  #1915 = Utf8               getMetadataRedisKey
  #1916 = Utf8               getMetadataMd5RedisKey
  #1919 = Utf8               tenantMD5RedisKey
  #1921 = Utf8               ()Lorg/springframework/data/redis/core/HashOperations;
  #1924 = Utf8               org/springframework/data/redis/core/HashOperations
  #1927 = Utf8               ()Lorg/springframework/data/redis/core/ValueOperations;
```

## `MetadataModifyAppService.javap.txt`
```text
   #5 = Methodref          #47.#48        // com/seeyon/ctp/metadata/domain/service/MetadataService.modifyEntityAttribute:(Lcom/seeyon/ctp/metadata/dto/request/EntityAttributeModifyDto;)Z
   #9 = Methodref          #47.#54        // com/seeyon/ctp/metadata/domain/service/MetadataService.coverAllModifyEntityAttribute:(Ljava/util/List;)Z
  #23 = Utf8               modifyEntityAttribute
  #34 = Utf8               coverAllModifyEntityAttribute
  #48 = NameAndType        #23:#61        // modifyEntityAttribute:(Lcom/seeyon/ctp/metadata/dto/request/EntityAttributeModifyDto;)Z
  #54 = NameAndType        #34:#68        // coverAllModifyEntityAttribute:(Ljava/util/List;)Z
  public com.seeyon.boot.transport.SingleResponse<java.lang.Boolean> modifyEntityAttribute(com.seeyon.boot.transport.SingleRequest<com.seeyon.ctp.metadata.dto.request.EntityAttributeModifyDto>);
        11: invokevirtual #5                  // Method com/seeyon/ctp/metadata/domain/service/MetadataService.modifyEntityAttribute:(Lcom/seeyon/ctp/metadata/dto/request/EntityAttributeModifyDto;)Z
  public com.seeyon.boot.transport.SingleResponse<java.lang.Boolean> coverAllModifyEntityAttribute(com.seeyon.boot.transport.SingleRequest<java.util.List<com.seeyon.ctp.metadata.dto.request.EntityAttributeModifyDto>>);
        11: invokevirtual #9                  // Method com/seeyon/ctp/metadata/domain/service/MetadataService.coverAllModifyEntityAttribute:(Ljava/util/List;)Z
```

## `MetadataCreateAppService.javap.txt`
```text
    #5 = Methodref          #156.#157     // com/seeyon/ctp/metadata/domain/service/MetadataService.createServiceMetadata:(Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;)Z
    #8 = Class              #162          // com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto
    #9 = Fieldref           #163.#164     // com/seeyon/ctp/metadata/enums/MetadataTypeEnum.RestApi:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
   #10 = Methodref          #8.#165       // com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getAppName:()Ljava/lang/String;
   #11 = Methodref          #8.#166       // com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getAppVersion:()Ljava/lang/String;
   #12 = Methodref          #8.#167       // com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getMetadatas:()Ljava/util/Map;
   #13 = Methodref          #156.#168     // com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
   #25 = Fieldref           #163.#174     // com/seeyon/ctp/metadata/enums/MetadataTypeEnum.Entity:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
   #55 = Methodref          #156.#187     // com/seeyon/ctp/metadata/domain/service/MetadataService.createJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)Z
   #87 = Utf8               createAllRestApiMetadata
   #88 = Utf8               Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;
   #89 = Utf8               Lcom/seeyon/boot/transport/SingleRequest<Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;>;
   #90 = Utf8               (Lcom/seeyon/boot/transport/SingleRequest<Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;>;)Lcom/seeyon/boot/transport/SingleResponse<Ljava/lang/Boolean;>;
   #91 = Utf8               ����ָ��Ӧ��RestApiԪ����
  #102 = Utf8               createAllEntityMetadata
  #127 = Utf8               createJSONMetadata
  #162 = Utf8               com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto
  #164 = NameAndType        #204:#205     // RestApi:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
  #168 = NameAndType        #211:#212     // createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
  #187 = NameAndType        #224:#225     // createJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)Z
  #204 = Utf8               RestApi
  #211 = Utf8               createMetadata
  #224 = Utf8               createJsonMetadata
        13: invokevirtual #5                  // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createServiceMetadata:(Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;)Z
  public com.seeyon.boot.transport.SingleResponse<java.lang.Boolean> createAllRestApiMetadata(com.seeyon.boot.transport.SingleRequest<com.seeyon.ctp.metadata.dto.request.ServiceRestApiMetadataDto>);
         4: checkcast     #8                  // class com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto
        12: getstatic     #9                  // Field com/seeyon/ctp/metadata/enums/MetadataTypeEnum.RestApi:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
        16: invokevirtual #10                 // Method com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getAppName:()Ljava/lang/String;
        20: invokevirtual #11                 // Method com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getAppVersion:()Ljava/lang/String;
        24: invokevirtual #12                 // Method com/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto.getMetadatas:()Ljava/util/Map;
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
            8      30     2   dto   Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;
            0      38     1 request   Lcom/seeyon/boot/transport/SingleRequest<Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;>;
    Signature: #90                          // (Lcom/seeyon/boot/transport/SingleRequest<Lcom/seeyon/ctp/metadata/dto/request/ServiceRestApiMetadataDto;>;)Lcom/seeyon/boot/transport/SingleResponse<Ljava/lang/Boolean;>;
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
  public com.seeyon.boot.transport.SingleResponse<java.lang.Boolean> createAllEntityMetadata(com.seeyon.boot.transport.SingleRequest<com.seeyon.ctp.metadata.dto.request.ServiceEntityMetadataDto>);
        12: getstatic     #25                 // Field com/seeyon/ctp/metadata/enums/MetadataTypeEnum.Entity:Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
  public com.seeyon.boot.transport.SingleResponse<java.lang.Boolean> createJSONMetadata(com.seeyon.boot.transport.SingleRequest<com.seeyon.ctp.metadata.dto.request.ServiceJsonMetadataDto>);
        32: invokevirtual #55                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createJsonMetadata:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/io/InputStream;)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
        28: invokevirtual #13                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.createMetadata:(Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/lang/String;Ljava/lang/String;Ljava/util/Map;Z)Z
```

## `MetadataDeleteAppService.javap.txt`
```text
    #5 = Methodref          #65.#66       // com/seeyon/ctp/metadata/domain/service/MetadataService.removeMetadataByAppName:(Ljava/lang/String;)Z
   #19 = Methodref          #65.#84       // com/seeyon/ctp/metadata/domain/service/MetadataService.removeTenantMetadataByFullNames:(Ljava/lang/String;Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/util/List;)Z
        11: invokevirtual #5                  // Method com/seeyon/ctp/metadata/domain/service/MetadataService.removeMetadataByAppName:(Ljava/lang/String;)Z
        71: invokevirtual #19                 // Method com/seeyon/ctp/metadata/domain/service/MetadataService.removeTenantMetadataByFullNames:(Ljava/lang/String;Lcom/seeyon/ctp/metadata/enums/MetadataTypeEnum;Ljava/util/List;)Z
```

## `MetadataController.javap.txt`
```text
Classfile /<XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/metadata-5.3.358/MetadataController.class
  Compiled from "MetadataController.java"
public class com.seeyon.ctp.metadata.controller.MetadataController extends com.seeyon.boot.starter.web.BaseComponentController
    #11 = Fieldref           #321.#886    // com/seeyon/ctp/metadata/controller/MetadataController.HTML_CACHE:Lcom/google/common/cache/Cache;
    #12 = Fieldref           #321.#887    // com/seeyon/ctp/metadata/controller/MetadataController.metadataQueryAppService:Lcom/seeyon/ctp/metadata/api/MetadataQueryAppService;
    #27 = Methodref          #888.#904    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #28 = Methodref          #888.#905    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
    #29 = Methodref          #888.#906    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #30 = Methodref          #888.#907    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
    #33 = Methodref          #888.#909    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadata:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #40 = Methodref          #888.#919    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #41 = Methodref          #888.#920    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
    #67 = Methodref          #888.#946    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #68 = Methodref          #888.#947    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
    #69 = Methodref          #888.#948    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #70 = Methodref          #888.#949    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
    #71 = Methodref          #888.#950    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #72 = Methodref          #888.#951    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
    #74 = Methodref          #888.#953    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #75 = Methodref          #888.#954    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
    #78 = Methodref          #888.#957    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #79 = Methodref          #888.#958    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
    #80 = Methodref          #888.#959    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
    #81 = Methodref          #888.#960    // com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #121 = Methodref          #119.#1002   // com/seeyon/ctp/metadata/domain/service/MetadataService.downgrade:()V
   #128 = Methodref          #119.#1009   // com/seeyon/ctp/metadata/domain/service/MetadataService.upgradeByAppName:(Ljava/lang/String;Ljava/util/List;)V
   #130 = Methodref          #119.#1012   // com/seeyon/ctp/metadata/domain/service/MetadataService.asyncUpgrade:()V
   #142 = Methodref          #119.#1029   // com/seeyon/ctp/metadata/domain/service/MetadataService.downgradeStarterMetadata:(Ljava/lang/String;Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
   #143 = Fieldref           #321.#1030   // com/seeyon/ctp/metadata/controller/MetadataController.redisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
   #144 = Methodref          #1031.#1032  // org/springframework/data/redis/core/RedisTemplate.opsForValue:()Lorg/springframework/data/redis/core/ValueOperations;
   #145 = Methodref          #1033.#1034  // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.serviceMetadataChangeRedisKey:()Ljava/lang/String;
   #154 = InterfaceMethodref #1043.#1044  // org/springframework/data/redis/core/ValueOperations.set:(Ljava/lang/Object;Ljava/lang/Object;JLjava/util/concurrent/TimeUnit;)V
   #158 = Methodref          #119.#1049   // com/seeyon/ctp/metadata/domain/service/MetadataService.refresh:(Ljava/lang/String;)V
   #163 = Methodref          #321.#1054   // com/seeyon/ctp/metadata/controller/MetadataController.downgrade:()Lcom/seeyon/boot/transport/SingleResponse;
   #195 = Methodref          #321.#1088   // com/seeyon/ctp/metadata/controller/MetadataController.printAppList:(Ljavax/servlet/http/HttpServletRequest;Ljavax/servlet/http/HttpServletResponse;)V
   #196 = Methodref          #321.#1089   // com/seeyon/ctp/metadata/controller/MetadataController.printFrontAppList:(Ljavax/servlet/http/HttpServletResponse;)V
   #220 = Class              #1114        // com/seeyon/ctp/metadata/controller/MetadataController$1
   #221 = Methodref          #220.#1115   // com/seeyon/ctp/metadata/controller/MetadataController$1."<init>":(Lcom/seeyon/ctp/metadata/controller/MetadataController;Ljava/lang/String;)V
   #253 = Class              #1149        // com/seeyon/ctp/metadata/controller/MetadataController$2
   #254 = Methodref          #253.#1150   // com/seeyon/ctp/metadata/controller/MetadataController$2."<init>":(Lcom/seeyon/ctp/metadata/controller/MetadataController;)V
   #267 = Class              #1161        // com/seeyon/ctp/metadata/controller/MetadataController$3
   #268 = Methodref          #267.#1150   // com/seeyon/ctp/metadata/controller/MetadataController$3."<init>":(Lcom/seeyon/ctp/metadata/controller/MetadataController;)V
   #269 = Methodref          #321.#1162   // com/seeyon/ctp/metadata/controller/MetadataController.getAppStartTimeMapFromRedis:()Ljava/util/Map;
   #281 = Methodref          #321.#1173   // com/seeyon/ctp/metadata/controller/MetadataController.outPrintServiceInfo:(Ljava/io/PrintWriter;Lcom/seeyon/ctp/metadata/dto/ServiceMetadataDto;Ljava/lang/String;)V
   #293 = Methodref          #1031.#1186  // org/springframework/data/redis/core/RedisTemplate.opsForHash:()Lorg/springframework/data/redis/core/HashOperations;
   #294 = InterfaceMethodref #1187.#1188  // org/springframework/data/redis/core/HashOperations.entries:(Ljava/lang/Object;)Ljava/util/Map;
   #321 = Class              #1233        // com/seeyon/ctp/metadata/controller/MetadataController
   #323 = Fieldref           #321.#1236   // com/seeyon/ctp/metadata/controller/MetadataController.log:Lorg/slf4j/Logger;
   #332 = Utf8               redisTemplate
   #333 = Utf8               Lorg/springframework/data/redis/core/RedisTemplate;
   #346 = Utf8               Lcom/seeyon/ctp/metadata/controller/MetadataController;
   #350 = Utf8               Lcom/seeyon/boot/annotation/RestApiOperation;
   #370 = Utf8               Lorg/springframework/web/bind/annotation/PostMapping;
   #418 = Utf8               selectRestApiMetadata
   #422 = Utf8               (Lcom/seeyon/ctp/metadata/dto/request/SearchMetadataDto;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
   #425 = Utf8               selectRestApiMetadataForPage
   #430 = Utf8               (Lcom/seeyon/boot/transport/PageDtoRequest<Lcom/seeyon/ctp/metadata/dto/request/SearchPageDto;>;)Lcom/seeyon/boot/transport/PageResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
   #434 = Utf8               selectRestApiMetadataByFullNames
   #437 = Utf8               (Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNamesDto;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
   #440 = Utf8               selectRestApiMetadataByFullName
   #443 = Utf8               (Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Lcom/seeyon/boot/transport/SingleResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
   #448 = Utf8               restApiMetadata
   #451 = Utf8               Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
   #456 = Utf8               selectRestApiMetadataExcludeBoot
   #459 = Utf8               selectRestApiMetadataExcludeBootForPage
   #550 = Utf8               selectEntityMetadata
   #554 = Utf8               selectEntityMetadataForPage
   #558 = Utf8               selectEntityMetadataByFullNames
   #562 = Utf8               selectEntityMetadataByFullName
   #566 = Utf8               selectEntityMetadataExcludeBoot
   #569 = Utf8               selectEntityMetadataExcludeBootForPage
   #575 = Utf8               selectAppServiceMetadata
   #579 = Utf8               selectAppServiceMetadataForPage
   #589 = Utf8               selectAppServiceMetadataByFullNames
   #593 = Utf8               selectAppServiceMetadataByFullName
   #597 = Utf8               selectAppServiceMetadataExcludeBoot
   #600 = Utf8               selectAppServiceMetadataExcludeBootForPage
   #810 = Class              #1233        // com/seeyon/ctp/metadata/controller/MetadataController
   #840 = Utf8               getAppStartTimeMapFromRedis
   #860 = Utf8               lambda$getAppStartTimeMapFromRedis$1
   #864 = Utf8               lambda$getAppStartTimeMapFromRedis$0
   #872 = Utf8               MetadataController.java
   #874 = Utf8               Lorg/springframework/web/bind/annotation/RequestMapping;
   #876 = Utf8               Lcom/seeyon/boot/annotation/RestApi;
   #904 = NameAndType        #1265:#1263  // selectRestApiMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #905 = NameAndType        #425:#426    // selectRestApiMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #906 = NameAndType        #434:#1263   // selectRestApiMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #907 = NameAndType        #440:#1262   // selectRestApiMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
   #909 = NameAndType        #418:#1263   // selectRestApiMetadata:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #919 = NameAndType        #1276:#1263  // selectRestApiMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #920 = NameAndType        #459:#426    // selectRestApiMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #946 = NameAndType        #1284:#1263  // selectEntityMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #947 = NameAndType        #554:#426    // selectEntityMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #948 = NameAndType        #558:#1263   // selectEntityMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #949 = NameAndType        #562:#1262   // selectEntityMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
   #950 = NameAndType        #1285:#1263  // selectEntityMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #951 = NameAndType        #569:#426    // selectEntityMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #953 = NameAndType        #1287:#1263  // selectAppServiceMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #954 = NameAndType        #579:#426    // selectAppServiceMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
   #957 = NameAndType        #589:#1263   // selectAppServiceMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #958 = NameAndType        #593:#1262   // selectAppServiceMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
   #959 = NameAndType        #1289:#1263  // selectAppServiceMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
   #960 = NameAndType        #600:#426    // selectAppServiceMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
  #1030 = NameAndType        #332:#333    // redisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
  #1031 = Class              #1340        // org/springframework/data/redis/core/RedisTemplate
  #1032 = NameAndType        #1341:#1342  // opsForValue:()Lorg/springframework/data/redis/core/ValueOperations;
  #1033 = Class              #1343        // com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils
  #1034 = NameAndType        #1344:#1321  // serviceMetadataChangeRedisKey:()Ljava/lang/String;
  #1043 = Class              #1353        // org/springframework/data/redis/core/ValueOperations
  #1114 = Utf8               com/seeyon/ctp/metadata/controller/MetadataController$1
  #1115 = NameAndType        #340:#1396   // "<init>":(Lcom/seeyon/ctp/metadata/controller/MetadataController;Ljava/lang/String;)V
  #1149 = Utf8               com/seeyon/ctp/metadata/controller/MetadataController$2
  #1150 = NameAndType        #340:#1409   // "<init>":(Lcom/seeyon/ctp/metadata/controller/MetadataController;)V
  #1161 = Utf8               com/seeyon/ctp/metadata/controller/MetadataController$3
  #1162 = NameAndType        #840:#841    // getAppStartTimeMapFromRedis:()Ljava/util/Map;
  #1186 = NameAndType        #1425:#1426  // opsForHash:()Lorg/springframework/data/redis/core/HashOperations;
  #1187 = Class              #1427        // org/springframework/data/redis/core/HashOperations
  #1196 = MethodHandle       #6:#1437     // invokestatic com/seeyon/ctp/metadata/controller/MetadataController.lambda$getAppStartTimeMapFromRedis$0:(Ljava/lang/Double;Ljava/lang/Double;)I
  #1209 = MethodHandle       #6:#1449     // invokestatic com/seeyon/ctp/metadata/controller/MetadataController.lambda$getAppStartTimeMapFromRedis$1:(Ljava/lang/Double;Ljava/lang/Double;)Ljava/lang/Double;
  #1233 = Utf8               com/seeyon/ctp/metadata/controller/MetadataController
  #1265 = Utf8               selectRestApiMetadataList
  #1276 = Utf8               selectRestApiMetadataListExcludeBoot
  #1284 = Utf8               selectEntityMetadataList
  #1285 = Utf8               selectEntityMetadataListExcludeBoot
  #1287 = Utf8               selectAppServiceMetadataList
  #1289 = Utf8               selectAppServiceMetadataListExcludeBoot
  #1340 = Utf8               org/springframework/data/redis/core/RedisTemplate
  #1342 = Utf8               ()Lorg/springframework/data/redis/core/ValueOperations;
  #1343 = Utf8               com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils
  #1344 = Utf8               serviceMetadataChangeRedisKey
  #1353 = Utf8               org/springframework/data/redis/core/ValueOperations
  #1396 = Utf8               (Lcom/seeyon/ctp/metadata/controller/MetadataController;Ljava/lang/String;)V
  #1409 = Utf8               (Lcom/seeyon/ctp/metadata/controller/MetadataController;)V
  #1426 = Utf8               ()Lorg/springframework/data/redis/core/HashOperations;
  #1427 = Utf8               org/springframework/data/redis/core/HashOperations
  #1437 = Methodref          #321.#1472   // com/seeyon/ctp/metadata/controller/MetadataController.lambda$getAppStartTimeMapFromRedis$0:(Ljava/lang/Double;Ljava/lang/Double;)I
  #1449 = Methodref          #321.#1473   // com/seeyon/ctp/metadata/controller/MetadataController.lambda$getAppStartTimeMapFromRedis$1:(Ljava/lang/Double;Ljava/lang/Double;)Ljava/lang/Double;
  #1472 = NameAndType        #864:#865    // lambda$getAppStartTimeMapFromRedis$0:(Ljava/lang/Double;Ljava/lang/Double;)I
  #1473 = NameAndType        #860:#861    // lambda$getAppStartTimeMapFromRedis$1:(Ljava/lang/Double;Ljava/lang/Double;)Ljava/lang/Double;
  private org.springframework.data.redis.core.RedisTemplate redisTemplate;
    descriptor: Lorg/springframework/data/redis/core/RedisTemplate;
  public com.seeyon.ctp.metadata.controller.MetadataController();
            0      30     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       8     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       8     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       8     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       8     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       8     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadata(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #27                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #422                         // (Lcom/seeyon/ctp/metadata/dto/request/SearchMetadataDto;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadataForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #28                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #430                         // (Lcom/seeyon/boot/transport/PageDtoRequest<Lcom/seeyon/ctp/metadata/dto/request/SearchPageDto;>;)Lcom/seeyon/boot/transport/PageResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadataByFullNames(com.seeyon.ctp.metadata.dto.request.SearchByFullNamesDto);
         8: invokevirtual #29                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #437                         // (Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNamesDto;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
  public com.seeyon.boot.transport.SingleResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadataByFullName(com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto);
         8: invokevirtual #30                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #443                         // (Lcom/seeyon/ctp/metadata/dto/request/SearchByFullNameDto;)Lcom/seeyon/boot/transport/SingleResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
        16: invokevirtual #33                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadata:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      61     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
           20      41     3 restApiMetadata   Lcom/seeyon/boot/transport/ListResponse;
           20      41     3 restApiMetadata   Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadataExcludeBoot(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #40                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #422                         // (Lcom/seeyon/ctp/metadata/dto/request/SearchMetadataDto;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.RestApiMetadataDto> selectRestApiMetadataExcludeBootForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #41                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectRestApiMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
    Signature: #430                         // (Lcom/seeyon/boot/transport/PageDtoRequest<Lcom/seeyon/ctp/metadata/dto/request/SearchPageDto;>;)Lcom/seeyon/boot/transport/PageResponse<Lcom/seeyon/ctp/metadata/dto/RestApiMetadataDto;>;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadata(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #67                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadataForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #68                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadataByFullNames(com.seeyon.ctp.metadata.dto.request.SearchByFullNamesDto);
         8: invokevirtual #69                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.SingleResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadataByFullName(com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto);
         8: invokevirtual #70                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadataExcludeBoot(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #71                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.EntityMetadataDto> selectEntityMetadataExcludeBootForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #72                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectEntityMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadata(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #74                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataList:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadataForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #75                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadataByFullNames(com.seeyon.ctp.metadata.dto.request.SearchByFullNamesDto);
         8: invokevirtual #78                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataByFullNames:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.SingleResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadataByFullName(com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto);
         8: invokevirtual #79                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataByFullName:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/SingleResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.ListResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadataExcludeBoot(com.seeyon.ctp.metadata.dto.request.SearchMetadataDto);
         8: invokevirtual #80                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataListExcludeBoot:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
  public com.seeyon.boot.transport.PageResponse<com.seeyon.ctp.metadata.dto.AppServiceMetadataDto> selectAppServiceMetadataExcludeBootForPage(com.seeyon.boot.transport.PageDtoRequest<com.seeyon.ctp.metadata.dto.request.SearchPageDto>);
         5: invokevirtual #81                 // Method com/seeyon/ctp/metadata/api/MetadataQueryAppService.selectAppServiceMetadataExcludeBootForPage:(Lcom/seeyon/boot/transport/PageDtoRequest;)Lcom/seeyon/boot/transport/PageResponse;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0       9     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0      12     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
        11: invokevirtual #121                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.downgrade:()V
            0      28     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
        28: invokevirtual #128                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.upgradeByAppName:(Ljava/lang/String;Ljava/util/List;)V
        50: invokevirtual #130                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.asyncUpgrade:()V
            0      67     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
        80: invokevirtual #142                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.downgradeStarterMetadata:(Ljava/lang/String;Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
       103: invokevirtual #142                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.downgradeStarterMetadata:(Ljava/lang/String;Ljava/lang/String;)Lcom/seeyon/ctp/metadata/dto/StarterMetadataDto;
            0     121     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
         1: getfield      #143                // Field redisTemplate:Lorg/springframework/data/redis/core/RedisTemplate;
         4: invokevirtual #144                // Method org/springframework/data/redis/core/RedisTemplate.opsForValue:()Lorg/springframework/data/redis/core/ValueOperations;
         7: invokestatic  #145                // Method com/seeyon/ctp/metadata/domain/util/MetadataRedisKeyUtils.serviceMetadataChangeRedisKey:()Ljava/lang/String;
        35: invokeinterface #154,  6          // InterfaceMethod org/springframework/data/redis/core/ValueOperations.set:(Ljava/lang/Object;Ljava/lang/Object;JLjava/util/concurrent/TimeUnit;)V
            0      46     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
        16: invokevirtual #158                // Method com/seeyon/ctp/metadata/domain/service/MetadataService.refresh:(Ljava/lang/String;)V
            0      74     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
            0     299     0  this   Lcom/seeyon/ctp/metadata/controller/MetadataController;
```
