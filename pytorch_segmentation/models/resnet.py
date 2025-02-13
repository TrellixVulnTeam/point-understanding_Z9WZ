# import torchvision
import math
import torch.nn as nn
import torch.utils.model_zoo as model_zoo
from .resnet_layers import (
        BasicBlock,
        Bottleneck)

# pylint: disable=too-many-instance-attributes


__all__ = ['ResNet', 'resnet18', 'resnet34', 'resnet50', 'resnet101',
           'resnet152']


model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
}


class ResNet(nn.Module):

    def __init__(self,
                 block,
                 layers,
                 num_classes=1000,
                 fully_conv=False,
                 remove_avg_pool_layer=False,
                 out_middle=False,
                 output_stride=32):

        # Add additional variables to track
        # output stride. Necessary to achieve
        # specified output stride.
        self.output_stride = output_stride
        self.current_stride = 4
        self.current_dilation = 1
        self.out_middle = out_middle

        self.remove_avg_pool_layer = remove_avg_pool_layer

        self.inplanes = 64
        self.fully_conv = fully_conv
        super(ResNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1, dilation=1):
        downsample = None

        if stride != 1 or self.inplanes != planes * block.expansion:

            # Check if we already achieved desired output stride.
            if self.current_stride == self.output_stride:

                # If so, replace subsampling with a dilation to preserve
                # current spatial resolution.
                self.current_dilation = self.current_dilation * stride
                stride = 1
            else:

                # If not, perform subsampling and update current
                # new output stride.
                self.current_stride = self.current_stride * stride

            # We don't dilate 1x1 convolution.
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(
            block(
                self.inplanes,
                planes,
                stride,
                downsample,
                dilation=self.current_dilation))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(
                block(
                    self.inplanes,
                    planes,
                    dilation=self.current_dilation))

        return nn.Sequential(*layers)

    def forward(self, x):
        y = list()
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        y.append(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        y.append(x)
        x = self.layer2(x)
        y.append(x)
        x = self.layer3(x)
        y.append(x)
        x = self.layer4(x)
        y.append(x)

        if self.out_middle:
            return x, y
        else:
            return x


def resnet18(pretrained=False, **kwargs):
    """Constructs a ResNet-18 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [2, 2, 2, 2], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet18']))
    return model


def resnet34(pretrained=False, **kwargs):
    """Constructs a ResNet-34 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(BasicBlock, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet34']))
    return model


def resnet50(pretrained=False, **kwargs):
    """Constructs a ResNet-50 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 6, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet50']))
    return model


def resnet101(pretrained=False, **kwargs):
    """Constructs a ResNet-101 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 4, 23, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet101']))
    return model


def resnet152(pretrained=False, **kwargs):
    """Constructs a ResNet-152 model.

    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet(Bottleneck, [3, 8, 36, 3], **kwargs)
    if pretrained:
        model.load_state_dict(model_zoo.load_url(model_urls['resnet152']))
    return model



class Resnet34_8s(nn.Module):
    
    def __init__(self, fully_conv=True, pretrained=True,
                 semseg_num_classes=21, objpart_num_classes=2):
       
        super(Resnet34_8s, self).__init__()
        
        
        # Load the pretrained weights, remove avg pool
        # layer and get the output stride of 8
        resnet34_32s = resnet34(fully_conv=fully_conv,
                                                   pretrained=pretrained,
                                                   output_stride=32,
                                                   remove_avg_pool_layer=True)
            
        resnet_block_expansion_rate = resnet34_32s.layer1[0].expansion

        # Create a linear layer -- we don't need logits in this case
        resnet34_32s.fc = nn.Sequential()

        self.resnet34_32s = resnet34_32s

        self.semseg_score_32s = nn.Conv2d(512 *  resnet_block_expansion_rate,
                                         semseg_num_classes,
                                         kernel_size=1)

        self.objpart_score_32s = nn.Conv2d(512 *  resnet_block_expansion_rate,
                                          objpart_num_classes,
                                          kernel_size=1)

        self.semseg_score_16s = nn.Conv2d(256 *  resnet_block_expansion_rate,
                                         semseg_num_classes,
                                         kernel_size=1)

        self.objpart_score_16s = nn.Conv2d(256 *  resnet_block_expansion_rate,
                                          objpart_num_classes,
                                          kernel_size=1)

        self.semseg_score_8s = nn.Conv2d(128 *  resnet_block_expansion_rate,
                                        semseg_num_classes,
                                        kernel_size=1)

        self.objpart_score_8s = nn.Conv2d(128 *  resnet_block_expansion_rate,
                                         objpart_num_classes,
                                         kernel_size=1)

    def forward(self, x):
        
        input_spatial_dim = x.size()[2:]
        
        x = self.resnet34_32s.conv1(x)
        x = self.resnet34_32s.bn1(x)
        x = self.resnet34_32s.relu(x)
        x = self.resnet34_32s.maxpool(x)
            
        x = self.resnet34_32s.layer1(x)
            
        x = self.resnet34_32s.layer2(x)
        semseg_logits_8s = self.semseg_score_8s(x)
        objpart_logits_8s = self.objpart_score_8s(x)
            
        x = self.resnet34_32s.layer3(x)
        semseg_logits_16s = self.semseg_score_16s(x)
        objpart_logits_16s = self.objpart_score_16s(x)
            
        x = self.resnet34_32s.layer4(x)
        semseg_logits_32s = self.semseg_score_32s(x)
        objpart_logits_32s = self.objpart_score_32s(x)
            
        logits_16s_spatial_dim = logits_16s.size()[2:]
        logits_8s_spatial_dim = logits_8s.size()[2:]
            
        semseg_logits_16s += nn.functional.upsample_bilinear(semseg_logits_32s,
                                                             size=logits_16s_spatial_dim)
                
        objpart_logits_16s += nn.functional.upsample_bilinear(objpart_logits_32s,
                                                           size=logits_16s_spatial_dim)

        semseg_logits_8s += nn.functional.upsample_bilinear(semseg_logits_16s,
                                                         size=logits_8s_spatial_dim)

        objpart_logits_8s += nn.functional.upsample_bilinear(objpart_logits_16s,
                                                          size=logits_8s_spatial_dim)

        semseg_logits_upsampled = nn.functional.upsample_bilinear(semseg_logits_8s,
                                                           size=input_spatial_dim)

        objpart_logits_upsampled = nn.functional.upsample_bilinear(objpart_logits_8s,
                                                                size=input_spatial_dim)

        return objpart_logits_upsampled, semseg_logits_upsampled


