/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.transport.ListResponse
 *  com.seeyon.boot.transport.SingleRequest
 *  com.seeyon.boot.transport.SingleResponse
 *  com.seeyon.bpm.dto.BpmConsistenceDetectionDto
 *  com.seeyon.bpm.dto.BpmDetectionEntityDto
 *  com.seeyon.bpm.dto.detection.DetectionAttrDeleteRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionAttrUpdateDto
 *  com.seeyon.bpm.dto.detection.DetectionAttrUpdateRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionCtpEnumDeleteRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionEntityDeleteRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionFullInfoRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionPageDeleteRequestDto
 *  com.seeyon.bpm.dto.detection.DetectionPageUpdateRequestDto
 */
package com.seeyon.bpm.api.udc;

import com.seeyon.boot.transport.ListResponse;
import com.seeyon.boot.transport.SingleRequest;
import com.seeyon.boot.transport.SingleResponse;
import com.seeyon.bpm.dto.BpmConsistenceDetectionDto;
import com.seeyon.bpm.dto.BpmDetectionEntityDto;
import com.seeyon.bpm.dto.detection.DetectionAttrDeleteRequestDto;
import com.seeyon.bpm.dto.detection.DetectionAttrUpdateDto;
import com.seeyon.bpm.dto.detection.DetectionAttrUpdateRequestDto;
import com.seeyon.bpm.dto.detection.DetectionCtpEnumDeleteRequestDto;
import com.seeyon.bpm.dto.detection.DetectionEntityDeleteRequestDto;
import com.seeyon.bpm.dto.detection.DetectionFullInfoRequestDto;
import com.seeyon.bpm.dto.detection.DetectionPageDeleteRequestDto;
import com.seeyon.bpm.dto.detection.DetectionPageUpdateRequestDto;

public interface BpmApiDetectionService {
    public ListResponse<BpmConsistenceDetectionDto> detectionForAttributeDelete(SingleRequest<DetectionAttrDeleteRequestDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detectionForAttributeUpdate(SingleRequest<DetectionAttrUpdateRequestDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detectionForCtpEnumDelete(SingleRequest<DetectionCtpEnumDeleteRequestDto> var1);

    public SingleResponse<Void> cascadeHandleAffectedForEntity(SingleRequest<BpmDetectionEntityDto> var1);

    public SingleResponse<Void> cascadeHandleAffectedForAttr(SingleRequest<DetectionAttrUpdateDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detectionForEntityDelete(SingleRequest<DetectionEntityDeleteRequestDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detectionForPageDelete(SingleRequest<DetectionPageDeleteRequestDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detectionForPageUpdate(SingleRequest<DetectionPageUpdateRequestDto> var1);

    public ListResponse<BpmConsistenceDetectionDto> detection(SingleRequest<DetectionFullInfoRequestDto> var1);
}
