/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.exception.BusinessException
 *  com.seeyon.boot.starter.udcrt.domain.service.FormHandlerFactory
 *  com.seeyon.boot.transport.PageResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.ctp.metadata.api.MetadataQueryAppService
 *  com.seeyon.ctp.metadata.dto.AppServiceMetadataDto
 *  com.seeyon.ctp.metadata.dto.AppServiceMethodMetadataDto
 *  com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto
 *  com.seeyon.udc.common.enums.ApplicationSourceEnum
 *  com.seeyon.udc.common.utils.BeanNameConvert
 *  com.seeyon.udc.common.utils.BeanNameConvert$SuffixEnum
 *  com.seeyon.udc.common.utils.UdcJsonUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.springframework.beans.factory.annotation.Autowired
 *  org.springframework.stereotype.Service
 */
package com.seeyon.boot.starter.udcrt.domain.service;

import com.seeyon.boot.exception.BusinessException;
import com.seeyon.boot.starter.udcrt.domain.service.FormHandlerFactory;
import com.seeyon.boot.transport.PageResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.ctp.metadata.api.MetadataQueryAppService;
import com.seeyon.ctp.metadata.dto.AppServiceMetadataDto;
import com.seeyon.ctp.metadata.dto.AppServiceMethodMetadataDto;
import com.seeyon.ctp.metadata.dto.request.SearchByFullNameDto;
import com.seeyon.udc.common.enums.ApplicationSourceEnum;
import com.seeyon.udc.common.utils.BeanNameConvert;
import com.seeyon.udc.common.utils.UdcJsonUtils;
import java.lang.reflect.Method;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class EntityAppServiceInvokeService {
    private static final Logger log = LoggerFactory.getLogger(EntityAppServiceInvokeService.class);
    @Autowired
    private MetadataQueryAppService metadataQueryAppService;

    public AppServiceMetadataDto findAppServiceMetaData(String aggEntityFullName, String appName) {
        String appServiceFullName = BeanNameConvert.entity4NameTo4Name((String)aggEntityFullName, (BeanNameConvert.SuffixEnum)BeanNameConvert.SuffixEnum.APPSERVICEIMPL);
        SearchByFullNameDto fullNameDto = new SearchByFullNameDto();
        fullNameDto.setFullName(appServiceFullName);
        fullNameDto.setAppName(appName);
        SingleResponse response = this.metadataQueryAppService.selectAppServiceMetadataByFullName(SingleRequest.from((Object)fullNameDto));
        if (!response.success() || response.getData() == null || response.getData().getContent() == null) {
            log.error("\u6839\u636e\u805a\u5408\u6839\u5b9e\u4f53\u83b7\u53d6appService\u5143\u6570\u636e\u5931\u8d25. param\uff1a\u3010{}\u3011", (Object)fullNameDto);
            throw new BusinessException("UDC_FORM_0001", new String[]{"AppService"});
        }
        return (AppServiceMetadataDto)response.getData().getContent();
    }

    public SingleResponse invokeMethod(AppServiceMetadataDto appServiceMetadata, String methodName, String data, String appName) {
        try {
            AppServiceMethodMetadataDto methodMetadata = appServiceMetadata.getMethods().stream().filter(e -> e.getFullName().endsWith(methodName)).findAny().get();
            String interfaceClass = methodMetadata.getInterfaceClass();
            Object bean = FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.NORMAL).getBeanObject(appName, interfaceClass);
            Method method = bean.getClass().getDeclaredMethod(methodName, SingleRequest.class);
            String paramFullNameDto = methodMetadata.getParameter().getItem().getItemType();
            Class<?> paramClazz = Class.forName(paramFullNameDto);
            Object paramDto = UdcJsonUtils.fromJson((String)data, paramClazz);
            SingleRequest singleRequest = SingleRequest.from((Object)paramDto);
            log.info("\u53cd\u5c04\u6267\u884c\u8868\u5355\u65b9\u6cd5, methodName: \u3010{}\u3011, request:\u3010{}\u3011,paramDto:\u3010{}\u3011", new Object[]{methodName, singleRequest, paramDto});
            return (SingleResponse)method.invoke(bean, singleRequest);
        }
        catch (Exception e2) {
            log.error("\u6267\u884c\u805a\u5408\u6839\u5b9e\u4f53appService\u65b9\u6cd5\u5931\u8d25\uff0cmethod:\u3010{}\u3011, data:\u3010{}\u3011", new Object[]{methodName, data, e2});
            throw new BusinessException("UDC_FORM_0002", new String[]{e2.getMessage()});
        }
    }

    public PageResponse invokePageMethod(AppServiceMetadataDto appServiceMetadata, String methodName, String data, String appName) {
        try {
            AppServiceMethodMetadataDto methodMetadata = appServiceMetadata.getMethods().stream().filter(e -> e.getFullName().endsWith(methodName)).findAny().get();
            String interfaceClass = methodMetadata.getInterfaceClass();
            Object bean = FormHandlerFactory.getFormHandler((ApplicationSourceEnum)ApplicationSourceEnum.NORMAL).getBeanObject(appName, interfaceClass);
            Method method = bean.getClass().getDeclaredMethod(methodName, SingleRequest.class);
            String paramFullNameDto = methodMetadata.getParameter().getItem().getItemType();
            Class<?> paramClazz = Class.forName(paramFullNameDto);
            Object paramDto = UdcJsonUtils.fromJson((String)data, paramClazz);
            SingleRequest singleRequest = SingleRequest.from((Object)paramDto);
            log.info("\u53cd\u5c04\u6267\u884c\u5b9e\u4f53\u65b9\u6cd5, methodName: \u3010{}\u3011, request:\u3010{}\u3011,paramDto:\u3010{}\u3011", new Object[]{methodName, singleRequest, paramDto});
            return (PageResponse)method.invoke(bean, singleRequest);
        }
        catch (Exception e2) {
            log.error("\u6267\u884c\u805a\u5408\u6839\u5b9e\u4f53appService\u65b9\u6cd5\u5931\u8d25\uff0cmethod:\u3010{}\u3011, data:\u3010{}\u3011", new Object[]{methodName, data, e2});
            throw new BusinessException("UDC_FORM_0002", new String[]{e2.getMessage()});
        }
    }
}
